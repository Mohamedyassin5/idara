"""
Louage Agent — Smoke Test
=========================

Runs louage_agent in isolation (without the hub or orchestrator) on a few
questions and prints the answers plus the tools it called.

Some questions carry an automatic regression check (code, not a second model call):
- the real-time schedule question must not contain any clock time other than the one
  asked in the question;
- the price question must not contain any dinar amount that is absent from louage_kb.md
  (the indicative ranges written there are the only allowed amounts).
The script exits with code 1 if a check fails or is inconclusive.

Usage (from the repo root):
    python scripts/test_louage_agent.py
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

from agents.mobility_city.louage_agent import (  # noqa: E402
    KB_FILE,
    load_louage_knowledge,
    louage_agent,
)

SCHEDULE_QUESTION = "Y a-t-il un louage de Tunis à Sousse ce soir à 20h ?"
PRICE_QUESTION = "Combien coûte un louage de Tunis à Sfax ?"

QUESTIONS = [
    "Comment fonctionne le système de louage en Tunisie ?",
    # Real-time data: must refuse to give a schedule, without inventing any time.
    SCHEDULE_QUESTION,
    # Must give the indicative range from the knowledge base, never an invented exact price.
    PRICE_QUESTION,
    # Off-topic: must decline without searching.
    "Quelle heure est-il ?",
]

# Voyage free tier without a payment method: 3 requests/minute, shared by indexing and
# knowledge searches. 21s between requests stays under it. Set to 0 once billing is added.
VOYAGE_PACING_SECONDS = 21

# Clock times: "20h", "20 h", "8h30", "20h 30", "20:00". Not durations written "3 heures"
# (a letter right after the "h" rejects the match). Durations written "2h" still match.
TIME_PATTERN = re.compile(r"(?<![\d.,])([01]?\d|2[0-3])(?:\s?h(?:\s?([0-5]\d))?|:([0-5]\d))(?!\w)", re.IGNORECASE)

# Dinar amounts, including ranges: "25 DT", "12,5 dinars", "20 à 40 DT", "entre 20 et 40 TND", "20-40 DT".
PRICE_PATTERN = re.compile(
    r"(?<![\d.,])(\d+(?:[.,]\d+)?)(?:\s*(?:à|-|–|et)\s*(\d+(?:[.,]\d+)?))?\s*(?:DT|TND|dinars?|د\.?ت|دينار)",
    re.IGNORECASE,
)


def find_times(text: str) -> dict[tuple[int, int], str]:
    """Map each clock time found in `text` to its first spelling, e.g. {(20, 0): "20h"}."""
    times: dict[tuple[int, int], str] = {}
    for match in TIME_PATTERN.finditer(text):
        minutes = match.group(2) or match.group(3) or "0"
        times.setdefault((int(match.group(1)), int(minutes)), match.group(0))
    return times


def find_prices(text: str) -> dict[float, str]:
    """Map each dinar amount found in `text` (both bounds of a range) to the matched text."""
    prices: dict[float, str] = {}
    for match in PRICE_PATTERN.finditer(text):
        for amount in (match.group(1), match.group(2)):
            if amount:
                prices.setdefault(float(amount.replace(",", ".")), match.group(0))
    return prices


def invented_times(answer: str) -> list[str]:
    """Clock times in the answer that come neither from the question nor from the knowledge base."""
    allowed = find_times(SCHEDULE_QUESTION).keys() | find_times(KB_FILE.read_text(encoding="utf-8")).keys()
    return [spelling for key, spelling in find_times(answer).items() if key not in allowed]


def ungrounded_prices(answer: str) -> list[str]:
    """Dinar amounts in the answer that are not written in the knowledge base."""
    allowed = find_prices(KB_FILE.read_text(encoding="utf-8")).keys()
    return [spelling for key, spelling in find_prices(answer).items() if key not in allowed]


# Regression checks: question -> (label of what is forbidden, function returning offending strings).
REGRESSION_CHECKS: dict[str, tuple[str, Callable[[str], list[str]]]] = {
    SCHEDULE_QUESTION: ("horaire inventé trouvé", invented_times),
    PRICE_QUESTION: ("prix absent de la base trouvé", ungrounded_prices),
}


def run_check(answer: str, tools: list[str], label: str, find_offenders: Callable[[str], list[str]]) -> bool:
    """Print a pass/fail verdict for one answer. Returns True on pass."""
    # A run that errored (rate limit, API error) returns the error text as content and calls
    # no tool: it contains nothing forbidden but proves nothing, so it must not count as a pass.
    if not answer.strip() or "search_knowledge_base" not in tools:
        print("❌ NON CONCLUANT : réponse vide ou aucune recherche dans la base (erreur API ou quota ?)")
        return False
    offenders = find_offenders(answer)
    if offenders:
        print(f"❌ RÉGRESSION : {label} : {', '.join(offenders)}")
        return False
    print(f"✅ Aucun élément interdit ({label.removesuffix(' trouvé')})")
    return True


def main() -> None:
    # Windows consoles default to cp1252; force UTF-8 so accents, emoji and Arabic script print.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("Chargement de la base de connaissances…")
    embedded = load_louage_knowledge(delay_seconds=VOYAGE_PACING_SECONDS)
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
        response = louage_agent.run(question)
        answer = response.content if isinstance(response.content, str) else str(response.content or "")
        print(answer)
        tools = [tool.tool_name for tool in (response.tools or [])]
        print(f"\n(outils appelés : {', '.join(tools) if tools else 'aucun'})")

        if question in REGRESSION_CHECKS:
            print()
            label, find_offenders = REGRESSION_CHECKS[question]
            if not run_check(answer, tools, label, find_offenders):
                failed_checks.append(f"[{i}] {question}")

    checked = sum(1 for question in QUESTIONS if question in REGRESSION_CHECKS)
    print("\n" + "=" * 80)
    if failed_checks:
        print(f"❌ {len(failed_checks)}/{checked} test(s) de régression en échec :")
        for failure in failed_checks:
            print(f"   - {failure}")
        sys.exit(1)
    print(f"✅ {checked}/{checked} test(s) de régression réussi(s)")


if __name__ == "__main__":
    main()
