"""
WhatsApp webhook checks (no Meta account or LLM call needed): command parsing, answer formatting, signature
check, background processing. The agent call and the Graph API call are replaced by recorders.

Run: python scripts/test_whatsapp.py
"""

import asyncio
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.update(WHATSAPP_APP_SECRET="s3cret", WHATSAPP_VERIFY_TOKEN="verify-me")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.whatsapp as wa  # noqa: E402

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


# --- command parsing ------------------------------------------------------------------------------------------
check("menu on bare slash", wa.parse_command("/") == ("menu", ""))
check("menu word", wa.parse_command("/Menu")[0] == "menu")
check("agent with question", wa.parse_command("/parking près de moi ?") == ("agent:parking-agent", "près de moi ?"))
check("agent alias + accent", wa.parse_command("/marché prix")[0] == "agent:souk-agent")
check("agent alone", wa.parse_command("/louage") == ("agent:louage-agent", ""))
check("unknown command", wa.parse_command("/xyz hello")[0] == "unknown")
check("plain text", wa.parse_command("bonjour") == ("", "bonjour"))
check("stop", wa.parse_command("/stop")[0] == "stop")

# --- formatting -------------------------------------------------------------------------------------------------
md = (
    "## Réponse\n**Station Moncef Bey** à Tunis.\n\n---\n\n**Prix** : 9 à 11 DT\n\n```geo\n"
    + json.dumps(
        {
            "type": "louage",
            "items": [
                {
                    "name": "Station Moncef Bey",
                    "lat": 36.79,
                    "lng": 10.18,
                    "destinations": [{"to": "Sousse", "tarif_indicatif": "9 à 11 DT", "duree_indicative": "2h"}],
                }
            ],
        }
    )
    + "\n```"
)
out = wa.to_whatsapp(md)
joined = "\n".join(out)
check("one message", len(out) == 1)
check("headings and bold converted", "*Réponse*" in joined and "**" not in joined and "##" not in joined)
check("geo block removed", "```" not in joined)
check("map link", "https://maps.google.com/?q=36.79,10.18" in joined)
check("louage destinations", "→ Sousse : 9 à 11 DT, 2h" in joined)
long = wa.to_whatsapp("\n\n".join(["x" * 1000] * 10))
check("long answer split under the limit", len(long) > 1 and all(len(c) <= wa.MAX_CHARS for c in long))

# --- conversation flow --------------------------------------------------------------------------------------
asked: list[tuple[str, str, str, str]] = []
sent: list[tuple[str, str]] = []


async def fake_ask(agent_id: str, message: str, session_id: str, user_id: str) -> str:
    asked.append((agent_id, message, session_id, user_id))
    return "**Réponse** ok"


async def fake_send(to: str, body: str) -> None:
    sent.append((to, body))


wa.ask_agent = fake_ask
wa.send_text = fake_send


async def flow() -> None:
    r = await wa.handle_text("216111", "salut")
    check("no agent yet -> menu", r == [wa.MENU])
    r = await wa.handle_text("216111", "/parking")
    check("agent selected without asking the model", "Stationnement" in r[0] and not asked)
    r = await wa.handle_text("216111", "où me garer ?")
    check("sticky agent", asked[-1][:2] == ("parking-agent", "où me garer ?") and r == ["*Réponse* ok"])
    check("session per phone, agent, epoch", asked[-1][2:] == ("wa-216111-parking-agent-0", "wa-216111"))
    await wa.handle_text("216111", "/souk prix des tomates ?")
    check("switch agent with a question", asked[-1][0] == "souk-agent" and asked[-1][1] == "prix des tomates ?")
    await wa.handle_text("216111", "/stop")
    await wa.handle_text("216111", "/souk encore")
    check("stop starts a new session", asked[-1][2] == "wa-216111-souk-agent-1")
    await wa.handle_text("216222", "/louage")
    check("users are isolated", wa._state["216222"]["agent"] == "louage-agent" and wa._state["216111"]["agent"] == "souk-agent")


asyncio.run(flow())

# --- webhook ------------------------------------------------------------------------------------------------------
api = FastAPI()
api.include_router(wa.router)
client = TestClient(api)


def post(payload: dict, secret: str = "s3cret") -> int:
    raw = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return client.post("/whatsapp/webhook", content=raw, headers={"x-hub-signature-256": sig}).status_code


def message(mid: str, **fields: object) -> dict:
    return {"entry": [{"changes": [{"value": {"messages": [{"id": mid, "from": "216333", **fields}]}}]}]}


r = client.get("/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "42"})
check("verification handshake", r.status_code == 200 and r.text == "42")
check("wrong verify token", client.get("/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "nope", "hub.challenge": "1"}).status_code == 403)
check("bad signature rejected", post(message("a1", type="text", text={"body": "/menu"}), secret="wrong") == 403)
check("missing signature rejected", client.post("/whatsapp/webhook", json={}).status_code == 403)


async def webhook_flow() -> None:
    sent.clear()
    asked.clear()
    with TestClient(api) as c:  # one running loop so the background tasks can finish
        for mid, body in (("m1", "/menu"), ("m1", "/menu")):  # same id twice: Meta retry
            raw = json.dumps(message(mid, type="text", text={"body": body})).encode()
            sig = "sha256=" + hmac.new(b"s3cret", raw, hashlib.sha256).hexdigest()
            assert c.post("/whatsapp/webhook", content=raw, headers={"x-hub-signature-256": sig}).status_code == 200
        raw = json.dumps(message("m2", type="location", location={"latitude": 36.8, "longitude": 10.1})).encode()
        sig = "sha256=" + hmac.new(b"s3cret", raw, hashlib.sha256).hexdigest()
        c.post("/whatsapp/webhook", content=raw, headers={"x-hub-signature-256": sig})
        raw = json.dumps(message("m3", type="image")).encode()
        sig = "sha256=" + hmac.new(b"s3cret", raw, hashlib.sha256).hexdigest()
        c.post("/whatsapp/webhook", content=raw, headers={"x-hub-signature-256": sig})
        await asyncio.sleep(0.3)


asyncio.run(webhook_flow())
check("duplicate delivery handled once", len(sent) == 3, f"{len(sent)} replies for 3 distinct messages")
check("location without an agent gets the menu", [b for _, b in sent].count(wa.MENU) == 2)
check("unsupported type gets a notice", any("texte" in b for _, b in sent))

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)
