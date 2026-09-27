"""
Bac Agent — Smoke Test
======================

Runs bac_agent in isolation (without the hub or orchestrator) on a few
questions and prints the answers plus the tools it called.

The exam-date question carries an automatic regression check (code, not a second model call):
the answer must contain no day/month date ("12 juin", "15/06", "juin 2026") and must contain an
explicit "I cannot know" formula. A bare month name ("les épreuves ont lieu en juin") is allowed:
that is the kind of general statement the knowledge base holds.
The script exits with code 1 if a check fails or is inconclusive.

Usage (from the repo root):
    python scripts/test_bac_agent.py
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

from agents.education_work.bac_agent import (  # noqa: E402
    bac_agent,
    load_bac_knowledge,
)

DATE_QUESTION = "Quelle est la date exacte de l'épreuve de maths cette année ?"

QUESTIONS = [
    "Quelles sont les sections du bac en Tunisie ?",
    "Comment fonctionne l'orientation universitaire après le bac ?",
    # Year-specific data: must refuse a date, explain it changes every year, invent nothing.
    DATE_QUESTION,
    # Off-topic: must decline without searching.
    "Quelle heure est-il ?",
]

# Voyage free tier without a payment method: 3 requests/minute, shared by indexing and
# knowledge searches. 21s between requests stays under it. Set to 0 once billing is added.
VOYAGE_PACING_SECONDS = 21

MONTHS = (
    r"(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)"
)

# Precise dates: "12 juin", "le 12 juin 2026", "juin 2026", "15/06", "15/06/2026", "15-06-2026", "2026-06-15".
DATE_PATTERN = re.compile(
    rf"(?:\d{{1,2}}\s*(?:er)?\s+{MONTHS}"  # 12 juin
    rf"|{MONTHS}\s+\d{{4}}"  # juin 2026
    r"|(?<![\d.,/])\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?(?![\d/-])"  # 15/06 or 15/06/2026
    r"|(?<![\d.,/])\d{4}-\d{1,2}-\d{1,2}(?![\d/-]))",  # 2026-06-15
    re.IGNORECASE,
)

# An answer about a year-specific date must contain at least one of these.
UNCERTAINTY_PATTERN = re.compile(
    r"(?:ne\s+(?:peux|peut|suis)\s+pas|n['’]ai\s+pas\s+(?:accès|d['’]information)|pas\s+en\s+mesure"
    r"|chaque\s+année|change(?:nt)?\s+chaque|impossible\s+de\s+(?:savoir|vous\s+dire)|je\s+ne\s+sais\s+pas"
    r"|pas\s+dans\s+ma\s+base)",
    re.IGNORECASE,
)


def check_date(answer: str) -> list[str]:
    """Precise dates in the answer, plus a missing refusal formula."""
    offenders = [f"date précise : « {match.group(0)} »" for match in DATE_PATTERN.finditer(answer)]
    if not UNCERTAINTY_PATTERN.search(answer):
        offenders.append("aucune formule d'incertitude (« je ne peux pas savoir », « change chaque année »…)")
    return offenders


# Regression checks: question -> (label of what is checked, function returning offending strings).
REGRESSION_CHECKS: dict[str, tuple[str, Callable[[str], list[str]]]] = {
    DATE_QUESTION: ("date inventée ou refus manquant", check_date),
}


def run_check(answer: str, tools: list[str], label: str, find_offenders: Callable[[str], list[str]]) -> bool:
    """Print a pass/fail verdict for one answer. Returns True on pass."""
    # A run that errored (rate limit, API error) returns the error text as content and calls
    # no tool: it proves nothing, so it must not count as a pass.
    if not answer.strip() or "search_knowledge_base" not in tools:
        print("❌ NON CONCLUANT : réponse vide ou aucune recherche dans la base (erreur API ou quota ?)")
        return False
    offenders = find_offenders(answer)
    if offenders:
        print(f"❌ RÉGRESSION ({label}) : {' | '.join(offenders)}")
        return False
    print(f"✅ Contrôle passé ({label})")
    return True


def main() -> None:
    # Windows consoles default to cp1252; force UTF-8 so accents, emoji and Arabic script print.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("Chargement de la base de connaissances…")
    embedded = load_bac_knowledge(delay_seconds=VOYAGE_PACING_SECONDS)
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
        response = bac_agent.run(question)
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
