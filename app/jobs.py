"""
Job Offers
==========

GET /jobs/offers — live job offers from the Adzuna API, returned in the same ```geo-compatible shape
the frontend already renders as a map + cards. Keys come from ADZUNA_APP_ID / ADZUNA_APP_KEY.
ADZUNA_COUNTRY selects the market (Adzuna's two-letter code, e.g. "fr", "gb").
"""

from os import getenv

import httpx
from fastapi import APIRouter, HTTPException

BASE_URL = "https://api.adzuna.com/v1/api/jobs"
TIMEOUT = 15.0

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def _offer_type(title: str, contract: str) -> str:
    text = f"{title} {contract}".lower()
    return "stage" if any(word in text for word in ("stage", "intern", "stagiaire")) else "emploi"


@router.get("/offers")
async def job_offers(what: str, where: str = "", results: int = 12) -> dict:
    app_id, app_key = getenv("ADZUNA_APP_ID"), getenv("ADZUNA_APP_KEY")
    country = getenv("ADZUNA_COUNTRY", "fr")
    if not app_id or not app_key:
        raise HTTPException(status_code=503, detail="Les offres ne sont pas configurées (clés Adzuna manquantes).")

    async def fetch(keywords: str) -> list[dict]:
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "what": keywords,
            "results_per_page": min(max(results, 1), 30),
            "content-type": "application/json",
        }
        if where:
            params["where"] = where
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.get(f"{BASE_URL}/{country}/search/1", params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="Le service d'offres ne répond pas, réessayez.") from exc
        return response.json().get("results", [])

    jobs = await fetch(what)
    words = what.split()
    if len(jobs) < 3 and len(words) > 2:
        jobs = await fetch(" ".join(words[:2]))

    items = []
    for job in jobs:
        lat, lng = job.get("latitude"), job.get("longitude")
        contract = job.get("contract_time") or job.get("contract_type") or ""
        items.append(
            {
                "id": str(job.get("id", "")),
                "name": job.get("title", ""),
                "company": (job.get("company") or {}).get("display_name", ""),
                "address": (job.get("location") or {}).get("display_name", ""),
                "category": _offer_type(job.get("title", ""), contract),
                "contract": contract,
                "salary_min": job.get("salary_min"),
                "url": job.get("redirect_url", ""),
                "lat": lat,
                "lng": lng,
            }
        )
    return {"type": "offer", "items": items}
