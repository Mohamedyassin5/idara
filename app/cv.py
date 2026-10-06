"""
CV Analysis
===========

POST /cv/analyze — the job agent's CV workspace. Reads an uploaded CV (PDF, TXT or MD), then asks
a structured-output agent to produce a card-ready analysis. Only what is written in the CV is used:
the model may point out gaps, but never invents an experience, a diploma or a skill.
"""

from io import BytesIO

import re
from os import getenv

from fastapi import APIRouter, HTTPException, UploadFile
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError
from pypdf import PdfReader

MAX_BYTES = 5 * 1024 * 1024
MAX_CHARS = 8_000

router = APIRouter(prefix="/cv", tags=["CV"])


class CvSkill(BaseModel):
    name: str
    level: str = Field(description="débutant, intermédiaire, avancé ou non précisé, d'après le CV uniquement")


class CvExperience(BaseModel):
    title: str
    organization: str = ""
    period: str = ""
    highlights: list[str] = Field(default_factory=list)


class SuggestedRole(BaseModel):
    title: str
    why: str
    match_percent: int = Field(ge=0, le=100)


class CvAnalysis(BaseModel):
    headline: str = Field(description="Une phrase qui résume le profil")
    score: int = Field(ge=0, le=100, description="Qualité du CV (structure, clarté, preuves), pas la valeur du candidat")
    strengths: list[str]
    gaps: list[str] = Field(description="Ce qui manque ou est faible dans le CV (sections, preuves, chiffres)")
    skills: list[CvSkill]
    experiences: list[CvExperience]
    suggested_roles: list[SuggestedRole]
    next_steps: list[str]


CV_INSTRUCTIONS = """\
Tu analyses un CV pour aider une personne à chercher du travail en Tunisie.
Règles :
1. Utilise UNIQUEMENT ce qui est écrit dans le CV. N'invente jamais une expérience, un diplôme, une compétence,
   une entreprise, une date ou un chiffre. Si une information manque, mets-la dans gaps, pas dans skills.
2. score mesure la qualité du CV (structure, clarté, preuves chiffrées), pas la valeur de la personne.
3. suggested_roles : postes plausibles au vu du CV, avec un pourcentage d'adéquation honnête et une raison courte.
4. next_steps : actions concrètes et réalisables (compléter une section, ajouter des résultats mesurables…).
5. Réponds en français, en vouvoyant, sauf si le CV est majoritairement en anglais (dans ce cas, en anglais).
6. Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour ni bloc de code, avec exactement les clés :
   headline, score, strengths, gaps, skills (name, level), experiences (title, organization, period, highlights),
   suggested_roles (title, why, match_percent), next_steps.
"""


def _redact_contacts(text: str) -> str:
    """Masks emails and phone numbers: the analysis never needs them, and the model gateway
    returns an empty answer for CVs that still carry contact details."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[email]", text)
    return re.sub(r"\+?\d[\d\s().-]{7,}\d", "[tel]", text)


def _extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        reader = PdfReader(BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if name.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="replace")
    raise HTTPException(status_code=415, detail="Format non supporté : PDF, TXT ou MD uniquement.")


@router.post("/analyze", response_model=CvAnalysis)
async def analyze_cv(file: UploadFile) -> CvAnalysis:
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (5 Mo maximum).")

    text = _redact_contacts(_extract_text(file.filename or "", data).strip())
    if len(text) < 40:
        raise HTTPException(status_code=422, detail="Impossible de lire le texte de ce CV (scan ou fichier vide ?).")

    for attempt in range(2):
        raw = await _ask_model(text)
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end == -1:
            print(f"cv attempt {attempt}: no JSON in reply ({len(raw)} chars)", flush=True)
            continue
        try:
            return CvAnalysis.model_validate_json(raw[start : end + 1])
        except ValidationError as exc:
            print(f"cv attempt {attempt}: invalid JSON ({len(raw)} chars): {exc.errors()[0]['msg']}", flush=True)
            continue
    raise HTTPException(status_code=502, detail="L'analyse n'a pas abouti, réessayez.")


async def _ask_model(text: str) -> str:
    client = AsyncOpenAI(base_url=getenv("LLM_BASE_URL"), api_key=getenv("LLM_API_KEY"), timeout=150)
    response = await client.chat.completions.create(
        model=getenv("LLM_MODEL", "claude-sonnet-5"),
        messages=[
            {"role": "system", "content": CV_INSTRUCTIONS},
            {"role": "user", "content": "CV à analyser :\n\n" + text[:MAX_CHARS]},
        ],
        max_tokens=8000,
    )
    return response.choices[0].message.content or ""
