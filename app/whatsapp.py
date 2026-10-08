"""
WhatsApp
========

Talk to the domain agents from WhatsApp (Meta WhatsApp Cloud API).

- GET  /whatsapp/webhook  Meta's verification handshake (WHATSAPP_VERIFY_TOKEN).
- POST /whatsapp/webhook  Incoming messages, authenticated by Meta's HMAC signature (WHATSAPP_APP_SECRET).

Users pick an agent with a slash command ("/parking", "/louage où prendre un louage pour Sousse ?").
"/parking" alone selects the agent and later messages keep going to it; "/menu" lists the agents.
Agents take 30-90 s to answer while Meta expects a reply within seconds, so the webhook acknowledges at once
and answers in a background task through the Graph API (WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID).
"""

import asyncio
import hashlib
import hmac
import json
import re
import time
from collections import deque
from os import getenv

import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from app.chat import ask_agent

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

GRAPH_URL = "https://graph.facebook.com/v21.0"
MAX_CHARS = 3800  # WhatsApp text messages are capped at 4096 characters
MAX_PLACES = 5

# command word -> agent id
COMMANDS: dict[str, str] = {
    "bureaucratie": "bureaucratie-agent",
    "bureau": "bureaucratie-agent",
    "admin": "bureaucratie-agent",
    "steg": "steg-agent",
    "sonede": "steg-agent",
    "entrepreneuriat": "entrepreneuriat-agent",
    "entreprise": "entrepreneuriat-agent",
    "louage": "louage-agent",
    "parking": "parking-agent",
    "souk": "souk-agent",
    "marche": "souk-agent",
    "bac": "bac-agent",
    "job": "job-agent",
    "emploi": "job-agent",
    "immobilier": "immobilier-agent",
    "immo": "immobilier-agent",
}

LABELS = {
    "bureaucratie-agent": "Démarches administratives",
    "steg-agent": "STEG & SONEDE",
    "entrepreneuriat-agent": "Entrepreneuriat",
    "louage-agent": "Louage & transport",
    "parking-agent": "Stationnement",
    "souk-agent": "Souks & marchés",
    "bac-agent": "Bac & orientation",
    "job-agent": "Emploi & stages",
    "immobilier-agent": "Immobilier",
}

MENU = (
    "*Idara* — votre assistant du quotidien en Tunisie\n\n"
    "Choisissez un agent avec une commande :\n"
    "/bureaucratie — démarches administratives\n"
    "/steg — STEG & SONEDE\n"
    "/entrepreneuriat — créer son activité\n"
    "/louage — louage & transport\n"
    "/parking — stationnement\n"
    "/souk — souks & marchés\n"
    "/bac — bac & orientation\n"
    "/job — emploi & stages\n"
    "/immobilier — logement\n\n"
    "Exemple : */louage station pour Sousse ?*\n"
    "Après */parking* seul, vos messages suivants vont à cet agent. */menu* pour revenir ici, */stop* pour "
    "recommencer une conversation."
)

# phone -> {"agent": agent id or "", "epoch": conversation counter}; lost on restart, which only resets the choice
_state: dict[str, dict] = {}
_busy: set[str] = set()
_seen: dict[str, None] = {}  # message ids already handled (Meta retries deliveries), insertion-ordered
_tasks: set[asyncio.Task] = set()
_STARTED_AT = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
_events: deque[dict] = deque(maxlen=20)  # recent activity for /whatsapp/diagnostics (no message content)


def _log(kind: str, phone: str = "", detail: str = "") -> None:
    _events.append({"at": time.strftime("%H:%M:%S", time.gmtime()), "kind": kind, "phone": f"...{phone[-4:]}" if phone else "", "detail": detail})


# ---------------------------------------------------------------------------
# Formatting: markdown answer -> WhatsApp text
# ---------------------------------------------------------------------------
_GEO_BLOCK = re.compile(r"```geo\s*([\s\S]*?)```")


def _split_geo(text: str) -> tuple[str, dict | None]:
    match = _GEO_BLOCK.search(text)
    if not match:
        return text, None
    try:
        payload = json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return text[: match.start()].strip(), None
    return text[: match.start()].strip(), payload if isinstance(payload, dict) else None


def _places(payload: dict) -> str:
    """The map result as text: name, detail and a Google Maps link for each place."""
    lines: list[str] = []
    for item in (payload.get("items") or [])[:MAX_PLACES]:
        name = item.get("name") or item.get("quartier") or ""
        if not name:
            continue
        lines.append(f"*{name}*")
        if payload.get("type") == "louage":
            lines += [f"  → {d['to']} : {d['tarif_indicatif']}, {d['duree_indicative']}" for d in item.get("destinations", [])]
        elif payload.get("type") == "immobilier":
            lines.append(f"  {item.get('loyer_indicatif_min')}–{item.get('loyer_indicatif_max')} {item.get('devise', '')}")
        elif item.get("address"):
            lines.append(f"  {item['address']}")
        if item.get("lat") is not None and item.get("lng") is not None:
            lines.append(f"  https://maps.google.com/?q={item['lat']},{item['lng']}")
        lines.append("")
    return "\n".join(lines).strip()


def to_whatsapp(markdown: str) -> list[str]:
    """Converts an agent's markdown answer into WhatsApp messages (bold syntax, map links, 4096-char limit)."""
    text, payload = _split_geo(markdown)
    text = re.sub(r"^#{1,6}\s*(.+?)\s*$", r"*\1*", text, flags=re.MULTILINE)  # headings -> bold
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)  # **bold** -> *bold*
    text = re.sub(r"^\s*-{3,}\s*$", "", text, flags=re.MULTILINE)  # horizontal rules
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if payload and (places := _places(payload)):
        text = f"{text}\n\n📍 *Sur la carte*\n{places}"

    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        if len(current) + len(paragraph) + 2 > MAX_CHARS and current:
            chunks.append(current)
            current = ""
        while len(paragraph) > MAX_CHARS:  # a single paragraph longer than a message
            chunks.append(paragraph[:MAX_CHARS])
            paragraph = paragraph[MAX_CHARS:]
        current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        chunks.append(current)
    return chunks or ["…"]


# ---------------------------------------------------------------------------
# Conversation logic
# ---------------------------------------------------------------------------
def parse_command(text: str) -> tuple[str, str]:
    """('menu'|'stop'|'agent:<id>'|'unknown'|'', rest of the message) for a slash command, else ('', text)."""
    text = text.strip()
    if not text.startswith("/"):
        return "", text
    head, _, rest = text[1:].partition(" ")
    word = re.sub(r"[^a-z]", "", head.lower().replace("é", "e").replace("è", "e"))
    rest = rest.strip()
    if word in ("", "menu", "help", "aide", "start", "agents"):
        return "menu", rest
    if word in ("stop", "reset", "new", "nouveau", "fin"):
        return "stop", rest
    if word in COMMANDS:
        return f"agent:{COMMANDS[word]}", rest
    return "unknown", rest


async def handle_text(phone: str, text: str) -> list[str]:
    """What to send back for one incoming message from `phone`."""
    state = _state.setdefault(phone, {"agent": "", "epoch": 0})
    command, rest = parse_command(text)

    if command == "menu":
        return [MENU]
    if command == "stop":
        state["agent"], state["epoch"] = "", state["epoch"] + 1
        return ["Conversation terminée. Choisissez un agent :\n\n" + MENU]
    if command == "unknown":
        return ["Commande inconnue.\n\n" + MENU]
    if command.startswith("agent:"):
        state["agent"] = command.removeprefix("agent:")
        if not rest:
            label = LABELS[state["agent"]]
            return [f"*{label}* activé. Posez votre question (en français, arabe ou derja). */menu* pour changer d'agent."]
    elif not state["agent"]:
        return [MENU]

    agent_id = state["agent"]
    session_id = f"wa-{phone}-{agent_id}-{state['epoch']}"
    answer = await ask_agent(agent_id, rest or text, session_id, f"wa-{phone}")
    return to_whatsapp(answer)


# ---------------------------------------------------------------------------
# Meta WhatsApp Cloud API
# ---------------------------------------------------------------------------
async def send_text(to: str, body: str) -> None:
    token, phone_id = getenv("WHATSAPP_ACCESS_TOKEN"), getenv("WHATSAPP_PHONE_NUMBER_ID")
    if not token or not phone_id:
        print("whatsapp: WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID missing, reply not sent", flush=True)
        _log("send_skipped", to, "access token or phone number id missing")
        return
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{GRAPH_URL}/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body, "preview_url": True}},
        )
    if response.status_code >= 400:
        print(f"whatsapp: send failed {response.status_code} {response.text[:200]}", flush=True)
        _log("send_failed", to, f"{response.status_code} {response.text[:160]}")
    else:
        _log("sent", to, str(response.status_code))


async def _process(phone: str, text: str) -> None:
    if phone in _busy:
        await send_text(phone, "Une réponse est déjà en cours pour vous, patientez un instant.")
        return
    _busy.add(phone)
    try:
        for chunk in await handle_text(phone, text):
            await send_text(phone, chunk)
    except Exception as exc:  # the user must always get an answer, whatever failed
        print(f"whatsapp: processing failed: {type(exc).__name__}: {exc}", flush=True)
        _log("agent_failed", phone, f"{type(exc).__name__}: {str(exc)[:160]}")
        await send_text(phone, "Désolé, une erreur est survenue. Réessayez dans un instant.")
    finally:
        _busy.discard(phone)


def _incoming_text(message: dict) -> str | None:
    """The text to forward for a WhatsApp message, or None when the type is not supported."""
    kind = message.get("type")
    if kind == "text":
        return (message.get("text") or {}).get("body", "")
    if kind == "location":
        loc = message.get("location") or {}
        return f"Ma position : latitude {loc.get('latitude')}, longitude {loc.get('longitude')}"
    return None


def _valid_signature(raw: bytes, header: str | None) -> bool:
    secret = getenv("WHATSAPP_APP_SECRET")
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


@router.get("/diagnostics")
async def diagnostics(request: Request, token: str = "", waba: str = "", subscribe: bool = False, app: str = "", register: bool = False) -> dict:
    """Recent bot activity and whether Meta accepts the access token. Protected by the verify token."""
    expected = getenv("WHATSAPP_VERIFY_TOKEN")
    if not expected or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="Forbidden")
    access, phone_id = getenv("WHATSAPP_ACCESS_TOKEN"), getenv("WHATSAPP_PHONE_NUMBER_ID")
    secret_value = getenv("WHATSAPP_APP_SECRET", "")
    meta: dict = {
        "configured": bool(access and phone_id),
        "app_secret_set": bool(secret_value),
        # Shape only, never the value: a Meta app secret is 32 hexadecimal characters.
        "app_secret_shape": f"{len(secret_value)} chars, {'hex' if re.fullmatch(r'[0-9a-fA-F]+', secret_value) else 'not hex'}"
        + (", has surrounding whitespace" if secret_value != secret_value.strip() else ""),
        "backend_started_at": _STARTED_AT,
    }
    if access and phone_id:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{GRAPH_URL}/{phone_id}", params={"fields": "display_phone_number,verified_name"}, headers={"Authorization": f"Bearer {access}"})
            meta["graph_status"] = response.status_code
            meta["graph"] = response.json() if response.status_code == 200 else response.json().get("error", {}).get("message", "")[:200]
        except httpx.HTTPError as exc:
            meta["graph_status"] = f"unreachable: {type(exc).__name__}"
    if access and re.fullmatch(r"\d{5,25}", waba):
        # Meta only delivers webhooks for a WhatsApp Business account the app is subscribed to.
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                headers = {"Authorization": f"Bearer {access}"}
                if subscribe:
                    done = await client.post(f"{GRAPH_URL}/{waba}/subscribed_apps", headers=headers)
                    meta["subscribe_status"] = done.status_code
                    meta["subscribe_result"] = done.json()
                listed = await client.get(f"{GRAPH_URL}/{waba}/subscribed_apps", headers=headers)
            meta["subscribed_apps"] = listed.json().get("data", listed.json().get("error", {}).get("message", ""))
        except httpx.HTTPError as exc:
            meta["subscribed_apps"] = f"unreachable: {type(exc).__name__}"
    secret = getenv("WHATSAPP_APP_SECRET")
    if secret and re.fullmatch(r"\d{5,25}", app):
        # The app's own webhook registration (callback URL and subscribed fields), read with the app token.
        app_token = {"access_token": f"{app}|{secret}"}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                if register:
                    callback = f"https://{request.headers.get('host', '')}/whatsapp/webhook"
                    done = await client.post(
                        f"{GRAPH_URL}/{app}/subscriptions",
                        params={**app_token, "object": "whatsapp_business_account", "callback_url": callback, "verify_token": expected, "fields": "messages"},
                    )
                    meta["register_status"] = done.status_code
                    meta["register_result"] = done.json()
                listed = await client.get(f"{GRAPH_URL}/{app}/subscriptions", params=app_token)
            body = listed.json()
            meta["app_subscriptions"] = body.get("data", body.get("error", {}).get("message", ""))
        except httpx.HTTPError as exc:
            meta["app_subscriptions"] = f"unreachable: {type(exc).__name__}"
    return {"meta": meta, "events": list(_events)}


@router.get("/info")
async def info() -> dict:
    """Public: the bot's number (digits only, international format) so the website can show a wa.me QR code."""
    return {"number": re.sub(r"\D", "", getenv("WHATSAPP_PUBLIC_NUMBER", ""))}


@router.get("/webhook")
async def verify(request: Request) -> Response:
    params = request.query_params
    expected = getenv("WHATSAPP_VERIFY_TOKEN")
    if expected and params.get("hub.mode") == "subscribe" and hmac.compare_digest(params.get("hub.verify_token", ""), expected):
        return Response(content=params.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive(request: Request) -> dict:
    raw = await request.body()
    if not getenv("WHATSAPP_APP_SECRET"):
        _log("rejected", "", "WHATSAPP_APP_SECRET is not set")
        raise HTTPException(status_code=503, detail="WhatsApp is not configured")
    if not _valid_signature(raw, request.headers.get("x-hub-signature-256")):
        has_header = bool(request.headers.get("x-hub-signature-256"))
        _log("rejected", "", "invalid signature: WHATSAPP_APP_SECRET does not match the app" if has_header else "missing signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    for entry in json.loads(raw).get("entry", []):
        for change in entry.get("changes", []):
            for message in (change.get("value") or {}).get("messages", []):
                message_id, phone = message.get("id", ""), message.get("from", "")
                if not phone or message_id in _seen:
                    continue
                _seen[message_id] = None
                _log("received", phone, f"type={message.get('type')}")
                while len(_seen) > 1000:
                    _seen.pop(next(iter(_seen)))
                text = _incoming_text(message)
                if text is None:
                    task = asyncio.create_task(send_text(phone, "Je comprends seulement le texte et la localisation pour le moment."))
                else:
                    task = asyncio.create_task(_process(phone, text))
                _tasks.add(task)
                task.add_done_callback(_tasks.discard)
    return {"status": "ok"}
