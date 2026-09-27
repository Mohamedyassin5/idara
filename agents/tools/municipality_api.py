"""
Municipality API Tool
=====================

Shared tool for querying the Tunisian Municipality API (https://tn-municipality-api.vercel.app).
Free, no API key required, server-side only (no CORS).

The API returns governorates, each containing a list of localities ("Delegations") with:
  Name, NameAr, Value, PostalCode, Latitude, Longitude

Call this tool when a user asks about the governorate, delegation or postal code of a
Tunisian city, neighbourhood or locality — it provides live, factual geo data that does
not belong in a static knowledge base.
"""

import json

import httpx
from agno.tools import tool

_BASE_URL = "https://tn-municipality-api.vercel.app"
_TIMEOUT = 5.0  # seconds


def _format_results(governorates: list[dict]) -> str:  # type: ignore[type-arg]
    """Flatten API response into a readable text the model can cite directly."""
    if not governorates:
        return "Aucun résultat trouvé pour ces critères."

    lines: list[str] = []
    for gov in governorates:
        gov_name: str = gov.get("Name", "?")
        gov_name_ar: str = gov.get("NameAr", "")
        delegations: list[dict] = gov.get("Delegations", [])  # type: ignore[type-arg]
        lines.append(f"Gouvernorat : {gov_name} ({gov_name_ar})")
        for d in delegations:
            loc_name = d.get("Name", "?")
            loc_ar = d.get("NameAr", "")
            postal = d.get("PostalCode", "")
            lat = d.get("Latitude", "")
            lng = d.get("Longitude", "")
            parts = [f"  - {loc_name} ({loc_ar})"]
            if postal:
                parts.append(f"code postal {postal}")
            if lat and lng:
                parts.append(f"coords {lat},{lng}")
            lines.append(", ".join(parts))
        lines.append("")

    return "\n".join(lines).strip()


@tool
def lookup_municipality(
    name: str | None = None,
    postal_code: str | None = None,
    delegation: str | None = None,
) -> str:
    """Search the Tunisian Municipality API for localisation information.

    Use this tool whenever the user asks:
    - which governorate (gouvernorat) a city, town, neighbourhood or locality belongs to
    - what the postal code (code postal) of a place is
    - which delegation (délégation) a place is in
    - any question requiring a live lookup of Tunisian administrative geography

    Do NOT use this tool for procedural / administrative questions (documents, fees, delays)
    — those are answered by search_knowledge_base.

    Args:
        name: Governorate or locality name to search for (e.g. "Ariana", "Sidi Thabet",
              "La Marsa"). Case-insensitive. Matches both governorate names and locality names.
        postal_code: Postal code to look up (e.g. "2058", "1000"). Optional.
        delegation: Delegation name to filter by (e.g. "Ariana Ville"). Optional.

    Returns:
        A formatted list of matching governorates and their localities with postal codes and
        coordinates, or an error message if the API is unreachable or returns no results.
    """
    params: dict[str, str] = {}
    if name:
        params["name"] = name
    if postal_code:
        params["postalCode"] = postal_code
    if delegation:
        params["delegation"] = delegation

    if not params:
        return "Erreur : au moins un critère de recherche est requis (nom, code postal ou délégation)."

    try:
        response = httpx.get(
            f"{_BASE_URL}/api/municipalities",
            params=params,
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data: list[dict] = response.json()  # type: ignore[type-arg]
        return _format_results(data)
    except httpx.TimeoutException:
        return "Erreur : l'API de localisation n'a pas répondu dans les délais (timeout 5s). Veuillez réessayer."
    except httpx.HTTPStatusError as exc:
        return f"Erreur HTTP {exc.response.status_code} lors de la requête à l'API de localisation."
    except (httpx.RequestError, json.JSONDecodeError) as exc:
        return f"Erreur lors de la connexion à l'API de localisation : {type(exc).__name__}."
