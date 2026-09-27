"""
Immobilier Agent — Smoke Test
=============================

Runs immobilier_agent in isolation (without the hub or orchestrator) on a few
questions and prints the answers plus the tools it called.

Automatic validation checks:
- Question 2 (current market price): must refuse to give an exact current price without
  inventing any dinar amount absent from immobilier_kb.md (regression test).
- Question 3 (geographic location): must call the `lookup_municipality` tool, not search_knowledge_base.

Usage (from the repo root):
    python scripts/test_immobilier_agent.py
"""

import re
import sys
import time
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evals.dotenv import load_dotenv  # noqa: E402

# Keys must be in os.environ before the model and embedder clients are built.
load_dotenv()

from agents.housing_community.immobilier_agent import (  # noqa: E402
    KB_FILE,
    immobilier_agent,
    load_immobilier_knowledge,
)

PRICE_QUESTION = "Combien coûte un appartement 2 pièces à Sfax en ce moment ?"
MUNICIPALITY_QUESTION = "Dans quel gouvernorat se trouve La Marsa ?"

QUESTIONS = [
    "Quels sont les pièges à éviter en cherchant un appartement à louer ?",
    PRICE_QUESTION,
    MUNICIPALITY_QUESTION,
    # Off-topic: must decline without searching.
    "Quelle heure est-il ?",
]

# Voyage free tier without a payment method: 3 requests/minute, shared by indexing and
# knowledge searches. 21s between requests stays under it. Set to 0 once billing is added.
VOYAGE_PACING_SECONDS = 21

# Dinar amounts, including ranges: "25 DT", "12,5 dinars", "20 à 40 DT", "entre 20 et 40 TND", "20-40 DT".
PRICE_PATTERN = re.compile(
    r"(?<![\d.,])(\d+(?:[.,]\d+)?)(?:\s*(?:à|-|–|et)\s*(\d+(?:[.,]\d+)?))?\s*(?:DT|TND|dinars?|د\.?ت|دينار)",
    re.IGNORECASE,
)


def find_prices(text: str) -> dict[float, str]:
    """Map each dinar amount found in `text` (both bounds of a range) to the matched text."""
    prices: dict[float, str] = {}
    for match in PRICE_PATTERN.finditer(text):
        for amount in (match.group(1), match.group(2)):
            if amount:
                prices.setdefault(float(amount.replace(",", ".")), match.group(0))
    return prices


def ungrounded_prices(answer: str) -> list[str]:
    """Dinar amounts in the answer that are not written in the knowledge base."""
    allowed = find_prices(KB_FILE.read_text(encoding="utf-8")).keys()
    return [spelling for key, spelling in find_prices(answer).items() if key not in allowed]


def run_price_check(answer: str, tools: list[str]) -> bool:
    """Validate that question 2 searched the KB, refused exact market prices, and invented no dinars."""
    if not answer.strip() or "search_knowledge_base" not in tools:
        print("❌ NON CONCLUANT : réponse vide ou aucune recherche dans la base (erreur API ou quota ?)")
        return False
    offenders = ungrounded_prices(answer)
    if offenders:
        print(f"❌ RÉGRESSION : prix absent de la base trouvé : {', '.join(offenders)}")
        return False
    print("✅ Aucun prix inventé trouvé (prix actuel refusé sans chiffre inventé)")
    return True


def run_municipality_check(answer: str, tools: list[str]) -> bool:
    """Validate that question 3 called lookup_municipality."""
    if not answer.strip():
        print("❌ NON CONCLUANT : réponse vide")
        return False
    if "lookup_municipality" not in tools:
        print(f"❌ ÉCHEC : l'outil lookup_municipality n'a pas été appelé (outils appelés : {', '.join(tools) if tools else 'aucun'})")
        return False
    print("✅ Outil lookup_municipality correctement appelé")
    return True


CHECKS: dict[str, tuple[str, Callable[[str, list[str]], bool]]] = {
    PRICE_QUESTION: ("prix refusé sans chiffre inventé", run_price_check),
    MUNICIPALITY_QUESTION: ("appel de l'outil lookup_municipality", run_municipality_check),
}


def main() -> None:
    # Windows consoles default to cp1252; force UTF-8 so accents, emoji and Arabic script print.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("Chargement de la base de connaissances…")
    embedded = load_immobilier_knowledge(delay_seconds=VOYAGE_PACING_SECONDS)
    print(f"{embedded} section(s) envoyée(s) à l'indexation.")
    if embedded and VOYAGE_PACING_SECONDS:
        print("Pause de 60s pour laisser se vider le quota Voyage avant les recherches…")
        time.sleep(60)

    failed_checks: list[str] = []
    for i, question in enumerate(QUESTIONS, start=1):
        if i > 1 and VOYAGE_PACING_SECONDS:
            time.sleep(VOYAGE_PACING_SECONDS)
        print("\n" + "=" * 80)
        print(f"[{i}/{len(QUESTIONS)}] {question}")
        print("-" * 80)
        response = immobilier_agent.run(question)
        answer = response.content if isinstance(response.content, str) else str(response.content or "")
        print(answer)
        tools = [tool.tool_name for tool in (response.tools or [])]
        print(f"\n(outils appelés : {', '.join(tools) if tools else 'aucun'})")

        if question in CHECKS:
            print()
            label, check_fn = CHECKS[question]
            if not check_fn(answer, tools):
                failed_checks.append(f"[{i}] {question}")

    checked = len(CHECKS)
    print("\n" + "=" * 80)
    if failed_checks:
        print(f"❌ {len(failed_checks)}/{checked} test(s) de validation en échec :")
        for failure in failed_checks:
            print(f"   - {failure}")
        sys.exit(1)
    print(f"✅ {checked}/{checked} test(s) de validation réussi(s)")


if __name__ == "__main__":
    main()
