"""
Municipality Tool — Test Script
================================

Two-part test:
  Part 1 — Unit tests the lookup_municipality function directly (no agent, no LLM),
            to validate the HTTP calls to the Tunisian Municipality API.
  Part 2 — Smoke-tests bureaucratie_agent with a localisation question to verify that
            it calls lookup_municipality and returns a grounded answer.

The script exits with code 1 if any check fails.

Usage (from the repo root):
    python scripts/test_municipality_tool.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evals.dotenv import load_dotenv  # noqa: E402

load_dotenv()

# ---------------------------------------------------------------------------
# Part 1 — Direct function tests (no agent)
# ---------------------------------------------------------------------------

from agents.tools.municipality_api import lookup_municipality  # noqa: E402


def call_tool(name=None, postal_code=None, delegation=None) -> str:
    """Call the underlying Python function, not the agno wrapper."""
    return lookup_municipality.entrypoint(
        name=name, postal_code=postal_code, delegation=delegation
    )


def test_by_name_ariana() -> bool:
    print("\n[1/3] lookup_municipality(name='Ariana')")
    result = call_tool(name="Ariana")
    print(result[:600])
    ok = "ARIANA" in result.upper() and "code postal" in result.lower()
    print("✅ OK" if ok else "❌ FAIL: expected ARIANA + code postal in response")
    return ok


def test_by_postal_code_2058() -> bool:
    print("\n[2/3] lookup_municipality(postal_code='2058')")
    result = call_tool(postal_code="2058")
    print(result[:600])
    ok = "2058" in result and "ARIANA" in result.upper()
    print("✅ OK" if ok else "❌ FAIL: expected 2058 and ARIANA in response")
    return ok


def test_by_name_sidi_thabet() -> bool:
    print("\n[3/3] lookup_municipality(name='Sidi Thabet')")
    result = call_tool(name="Sidi Thabet")
    print(result[:600])
    # Sidi Thabet is in Ariana governorate (postal 2032)
    ok = "ARIANA" in result.upper() and "SIDI THABET" in result.upper()
    print("✅ OK" if ok else "❌ FAIL: expected ARIANA and SIDI THABET in response")
    return ok


# ---------------------------------------------------------------------------
# Part 2 — Agent smoke test: bureaucratie_agent + lookup_municipality
# ---------------------------------------------------------------------------

from agents.admin_utilities.bureaucratie_agent import (  # noqa: E402
    bureaucratie_agent,
    load_bureaucratie_knowledge,
)

VOYAGE_PACING_SECONDS = 21

LOCALISATION_QUESTION = "Dans quel gouvernorat se trouve Sidi Thabet ?"


def test_agent_localisation() -> bool:
    import time

    print("\n" + "=" * 80)
    print(f"[AGENT] bureaucratie_agent — question : {LOCALISATION_QUESTION}")
    print("-" * 80)

    response = bureaucratie_agent.run(LOCALISATION_QUESTION)
    answer = response.content if isinstance(response.content, str) else str(response.content or "")
    print(answer)

    tools_called = [t.tool_name for t in (response.tools or [])]
    print(f"\n(outils appelés : {', '.join(tools_called) if tools_called else 'aucun'})")

    used_tool = "lookup_municipality" in tools_called
    has_ariana = "ariana" in answer.lower() or "ariena" in answer.lower()

    if not used_tool:
        print("❌ FAIL : lookup_municipality n'a pas été appelé")
        return False
    if not has_ariana:
        print("❌ FAIL : la réponse ne mentionne pas Ariana")
        return False
    print("✅ OK : outil appelé et réponse contient 'Ariana'")
    return True


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 80)
    print("PART 1 — Tests directs de lookup_municipality (sans agent)")
    print("=" * 80)

    unit_results = [
        test_by_name_ariana(),
        test_by_postal_code_2058(),
        test_by_name_sidi_thabet(),
    ]

    print("\n" + "=" * 80)
    print("PART 2 — Smoke test agent (charge la base de connaissances…)")
    print("=" * 80)
    embedded = load_bureaucratie_knowledge(delay_seconds=VOYAGE_PACING_SECONDS)
    print(f"{embedded} section(s) indexée(s) à la volée.")

    agent_result = test_agent_localisation()

    print("\n" + "=" * 80)
    all_passed = all(unit_results) and agent_result
    if all_passed:
        print("✅ Tous les tests ont réussi.")
    else:
        failed = unit_results.count(False) + (0 if agent_result else 1)
        print(f"❌ {failed} test(s) en échec.")
        sys.exit(1)


if __name__ == "__main__":
    main()
