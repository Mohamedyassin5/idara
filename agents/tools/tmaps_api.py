"""
TMaps API Tool
==============

Shared tool for querying the TMaps geocoding API (https://www.tmaps.tn), nearby-places endpoint:
GET https://api.tmaps.tn/geocoding/nearby

Requires an API key (account on app.tmaps.tn) in the TMAPS_API_KEY environment variable.

The API returns general points of interest (shops, services, schools, banks…) around a coordinate, each with:
  id, name, category, lat, lng, distance (metres), address, phone (optional), opening_hours (optional)

It is NOT a database of employers or job offers: it only lets an agent spot physical businesses in an area.
"""

import json
from os import getenv

import httpx
from agno.tools import tool

_BASE_URL = "https://api.tmaps.tn"
_TIMEOUT = 5.0  # seconds
_MAX_RADIUS_METERS = 10000
_DEFAULT_LIMIT = 20  # API default is 20, max 100
_CATEGORIES = frozenset(
    {
        "restaurant",
        "cafe",
        "school",
        "hospital",
        "pharmacy",
        "bank",
        "atm",
        "fuel",
        "hotel",
        "parking",
        "transit",
        "municipality",
        "health",
        "education",
        "shopping",
        "culture",
        "mosque",
        "place_of_worship",
    }
)


def _format_places(places: list[dict]) -> str:  # type: ignore[type-arg]
    """Flatten the API response into readable text the model can cite directly."""
    if not places:
        return "Aucun lieu trouvé pour ces critères."

    lines: list[str] = []
    for place in places:
        parts = [f"- {place.get('name') or '(sans nom)'}"]
        if place.get("category"):
            parts.append(f"catégorie : {place['category']}")
        if place.get("distance") is not None:
            parts.append(f"à {round(place['distance'])} m")
        if place.get("address"):
            parts.append(f"adresse : {place['address']}")
        if place.get("phone"):
            parts.append(f"téléphone : {place['phone']}")
        if place.get("opening_hours"):
            parts.append(f"horaires : {place['opening_hours']}")
        if place.get("lat") is not None and place.get("lng") is not None:
            parts.append(f"coords : {place['lat']},{place['lng']}")
        lines.append(", ".join(parts))
    return "\n".join(lines)


def places_to_geo_json(places: list[dict], geo_type: str) -> str:  # type: ignore[type-arg]
    """Build the exact ```geo payload an agent must copy verbatim after listing these places.

    Keeps only the fields the frontend map needs, straight from the API response, so the model
    never has to retype (and risk altering) a name or a coordinate by hand.
    """
    items = [
        {
            "id": p.get("id"),
            "name": p.get("name"),
            "lat": p.get("lat"),
            "lng": p.get("lng"),
            "category": p.get("category"),
            "address": p.get("address"),
            "phone": p.get("phone"),
            "distance_m": round(p["distance"]) if p.get("distance") is not None else None,
        }
        for p in places
        if p.get("lat") is not None and p.get("lng") is not None
    ]
    return json.dumps({"type": geo_type, "items": items}, ensure_ascii=False)


@tool
def find_nearby_places(
    lat: float,
    lng: float,
    radius_meters: int = 2000,
    categories: str | None = None,
    query: str | None = None,
    geo_type: str | None = None,
) -> str:
    """Find points of interest (shops, services, banks, schools…) around a GPS coordinate in Tunisia.

    Use this tool when the user wants to spot physical businesses or places in a given area, for example
    shops around a street to try a spontaneous application (candidature spontanée), and a location is
    available as coordinates (latitude/longitude) given by the user.

    IMPORTANT: results are general points of interest, NOT job offers and NOT a list of companies that are
    hiring. Never present them as vacancies. Do NOT use this tool to search for job offers, and do not
    invent coordinates: if no coordinates are available, ask the user for them.

    Args:
        lat: Latitude of the search centre (e.g. 36.8002 for central Tunis).
        lng: Longitude of the search centre (e.g. 10.1815 for central Tunis).
        radius_meters: Search radius in metres. Default 2000, maximum 10000 (larger values are capped).
        categories: Optional comma-separated categories among: restaurant, cafe, school, hospital,
                    pharmacy, bank, atm, fuel, hotel, parking, transit, municipality, health, education,
                    shopping, culture, mosque, place_of_worship (e.g. "shopping,cafe").
        query: Optional text filter on the place name (e.g. "boutique").
        geo_type: When set (e.g. "parking", "souk"), appends a ```geo fenced block built straight from
                  these results, for an agent whose instructions ask it to show the results on a map.
                  Leave unset for a plain text answer.

    Returns:
        A text list of places with name, category, distance in metres, address and phone number when
        available, or a clear error message if the API key is missing or the API is unreachable.
    """
    api_key = getenv("TMAPS_API_KEY")
    if not api_key:
        return "Erreur : la clé API TMaps n'est pas configurée (variable d'environnement TMAPS_API_KEY manquante)."

    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return "Erreur : coordonnées invalides (latitude entre -90 et 90, longitude entre -180 et 180)."
    if radius_meters <= 0:
        return "Erreur : le rayon de recherche doit être supérieur à 0 mètre."

    notes: list[str] = []
    if radius_meters > _MAX_RADIUS_METERS:
        radius_meters = _MAX_RADIUS_METERS
        notes.append(f"Note : rayon limité au maximum autorisé ({_MAX_RADIUS_METERS} m).")

    params: dict[str, str | float | int] = {
        "lat": lat,
        "lng": lng,
        "radius": radius_meters,
        "limit": _DEFAULT_LIMIT,
        "lang": "fr",
        "api_key": api_key,
    }
    if categories:
        requested = [c.strip().lower() for c in categories.split(",") if c.strip()]
        unknown = [c for c in requested if c not in _CATEGORIES]
        if unknown:
            return (
                f"Erreur : catégorie(s) inconnue(s) : {', '.join(unknown)}. "
                f"Catégories disponibles : {', '.join(sorted(_CATEGORIES))}."
            )
        if requested:
            params["categories"] = ",".join(requested)
    if query:
        params["q"] = query

    try:
        response = httpx.get(f"{_BASE_URL}/geocoding/nearby", params=params, timeout=_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except httpx.TimeoutException:
        return "Erreur : l'API TMaps n'a pas répondu dans les délais (timeout 5s). Veuillez réessayer."
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status in (401, 403):
            return f"Erreur HTTP {status} : la clé API TMaps est refusée (invalide ou sans droits)."
        return f"Erreur HTTP {status} lors de la requête à l'API TMaps."
    except (httpx.RequestError, json.JSONDecodeError) as exc:
        return f"Erreur lors de la connexion à l'API TMaps : {type(exc).__name__}."

    # The documented response is a list of POIs; tolerate a wrapping object just in case.
    if isinstance(data, dict):
        data = data.get("results") or data.get("data") or data.get("places") or []
    if not isinstance(data, list):
        return "Erreur : réponse inattendue de l'API TMaps."

    if not data and params.get("categories"):
        # The API's category coverage is partial (e.g. many places are tagged "other" and match no
        # documented category), so an empty filtered result does not mean the area has no places.
        notes.append(
            f"Aucun lieu trouvé pour la catégorie « {params['categories']} ». La couverture des catégories de "
            "TMaps est partielle : relancer la recherche sans le paramètre categories pour voir les lieux "
            "de tous types autour de ces coordonnées."
        )
        return "\n".join(notes)

    text = "\n".join([*notes, _format_places(data)])
    if geo_type:
        text += (
            "\n\nBloc à recopier tel quel, sans aucune modification, dans un ```geo ... ``` à LA FIN de ta "
            f"réponse :\n{places_to_geo_json(data, geo_type)}"
        )
    return text
