"""
Static Geo Reference Tool
=========================

Shared helper for agents that answer with named, located references from a small, hand-curated,
version-controlled JSON file (e.g. louage stations, indicative neighbourhood rents) rather than a
live API or the free-text knowledge base. The data is structured on purpose so it can be copied
verbatim into a ```geo fenced block and rendered on a map by the frontend, instead of being
retyped (and risking an altered name, price or coordinate) by the model.
"""

import json


def build_geo_block(items: list[dict], geo_type: str) -> str:  # type: ignore[type-arg]
    """Render the matching reference rows as text, followed by the exact ```geo payload to copy."""
    if not items:
        return "Aucune référence trouvée pour ces critères dans la table statique."
    payload = json.dumps({"type": geo_type, "items": items}, ensure_ascii=False)
    return (
        f"Références trouvées (table statique, {len(items)} résultat(s)) :\n"
        f"{json.dumps(items, ensure_ascii=False)}\n\n"
        "Bloc à recopier tel quel, sans aucune modification, dans un ```geo ... ``` à LA FIN de ta réponse :\n"
        f"{payload}"
    )
