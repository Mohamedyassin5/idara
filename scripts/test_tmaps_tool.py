"""
TMaps Tool — Test Script
========================

Two-part test:
  Part 1 — Calls find_nearby_places directly (no agent, no LLM) around central Tunis
            (36.8002, 10.1815) with categories="shopping", plus the local guard-rails
            (radius cap, unknown category) that never reach the API.
  Part 2 — Smoke-tests job_agent with a spontaneous-application question that carries the
            coordinates, to verify it calls find_nearby_places and states that the results
            are not confirmed job offers.

Requires TMAPS_API_KEY in .env (Part 1 network checks and Part 2 need it). The script exits
with code 1 if any check fails.

Usage (from the repo root):
    python scripts/test_tmaps_tool.py
"""

import sys
from os import getenv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evals.dotenv import load_dotenv  # noqa: E402

load_dotenv()

from agents.education_work.job_agent import job_agent, load_job_knowledge  # noqa: E402
from agents.tools.tmaps_api import find_nearby_places  # noqa: E402

VOYAGE_PACING_SECONDS = 21

TUNIS_LAT, TUNIS_LNG = 36.8002, 10.1815

AGENT_QUESTION = (
    "Je cherche du travail dans le commerce autour de l'avenue Habib Bourguiba à Tunis "
    f"(coordonnées : latitude {TUNIS_LAT}, longitude {TUNIS_LNG}), quelles boutiques sont à proximité "
    "pour tenter une candidature spontanée ?"
)


def call_tool(**kwargs) -> str:
    """Call the underlying Python function, not the agno wrapper."""
    return find_nearby_places.entrypoint(**kwargs)


def test_nearby_shopping_tunis() -> bool:
    print(f"\n[1/4] find_nearby_places(lat={TUNIS_LAT}, lng={TUNIS_LNG}, categories='shopping')")
    result = call_tool(lat=TUNIS_LAT, lng=TUNIS_LNG, radius_meters=2000, categories="shopping")
    print(result[:800])
    # TMaps' category coverage is partial: around central Tunis, "shopping" currently returns no place
    # (only e.g. restaurant/education are populated). A valid empty answer is therefore accepted, as long
    # as the call succeeded and the tool tells the model to retry without a category.
    if result.startswith("Erreur"):
        print("❌ FAIL: the API call failed")
        return False
    if "catégorie : shopping" in result:
        print("✅ OK : places found")
        return True
    ok = "sans le paramètre categories" in result
    print("✅ OK : réponse vide valide (couverture partielle), retry suggéré" if ok else "❌ FAIL: unexpected response")
    return ok


def test_nearby_no_category() -> bool:
    print(f"\n[2/4] find_nearby_places(lat={TUNIS_LAT}, lng={TUNIS_LNG}) sans catégorie")
    result = call_tool(lat=TUNIS_LAT, lng=TUNIS_LNG, radius_meters=1000)
    print(result[:600])
    ok = not result.startswith("Erreur") and "Aucun lieu" not in result and " m" in result
    print("✅ OK" if ok else "❌ FAIL: expected a list of places with names and distances")
    return ok


def test_radius_capped() -> bool:
    print("\n[3/4] find_nearby_places(radius_meters=50000) -> capped to 10000 m")
    result = call_tool(lat=TUNIS_LAT, lng=TUNIS_LNG, radius_meters=50000, categories="shopping")
    print(result[:300])
    ok = "rayon limité" in result and "10000" in result
    print("✅ OK" if ok else "❌ FAIL: expected the radius cap note")
    return ok


def test_unknown_category() -> bool:
    print("\n[4/4] find_nearby_places(categories='boulangerie') -> rejected locally")
    result = call_tool(lat=TUNIS_LAT, lng=TUNIS_LNG, categories="boulangerie")
    print(result[:300])
    ok = "inconnue" in result and "boulangerie" in result
    print("✅ OK" if ok else "❌ FAIL: expected an unknown-category error")
    return ok


def test_agent_spontaneous_application() -> bool:
    print("\n" + "=" * 80)
    print(f"[AGENT] job_agent — question : {AGENT_QUESTION}")
    print("-" * 80)

    response = job_agent.run(AGENT_QUESTION)
    answer = response.content if isinstance(response.content, str) else str(response.content or "")
    print(answer)

    tools_called = [t.tool_name for t in (response.tools or [])]
    print(f"\n(outils appelés : {', '.join(tools_called) if tools_called else 'aucun'})")

    if "find_nearby_places" not in tools_called:
        print("❌ FAIL : find_nearby_places n'a pas été appelé")
        return False
    lowered = answer.lower()
    if "offre" not in lowered and "recrut" not in lowered:
        print("❌ FAIL : la réponse ne précise pas que ce ne sont pas des offres d'emploi / entreprises qui recrutent")
        return False
    print("✅ OK : outil appelé et la réponse précise que ce ne sont pas des offres/recrutements confirmés")
    return True


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if not getenv("TMAPS_API_KEY"):
        print("❌ TMAPS_API_KEY est absente de l'environnement / .env : ajoutez-la avant de lancer ce test.")
        sys.exit(1)

    print("=" * 80)
    print("PART 1 — Tests directs de find_nearby_places (sans agent)")
    print("=" * 80)
    unit_results = [
        test_nearby_shopping_tunis(),
        test_nearby_no_category(),
        test_radius_capped(),
        test_unknown_category(),
    ]

    print("\n" + "=" * 80)
    print("PART 2 — Smoke test agent (charge la base de connaissances…)")
    print("=" * 80)
    embedded = load_job_knowledge(delay_seconds=VOYAGE_PACING_SECONDS)
    print(f"{embedded} section(s) indexée(s) à la volée.")

    agent_result = test_agent_spontaneous_application()

    print("\n" + "=" * 80)
    if all(unit_results) and agent_result:
        print("✅ Tous les tests ont réussi.")
    else:
        failed = unit_results.count(False) + (0 if agent_result else 1)
        print(f"❌ {failed} test(s) en échec.")
        sys.exit(1)


if __name__ == "__main__":
    main()
