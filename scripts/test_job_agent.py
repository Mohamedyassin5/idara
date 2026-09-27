"""
Job Agent — Smoke Test
======================

Runs job_agent in isolation (without the hub or orchestrator) on a few
questions and prints the answers plus the tools it called.

The SMIG question carries an automatic regression check (code, not a second model call):
the answer must contain no dinar amount that is absent from job_kb.md. Because the knowledge
base contains no monetary amounts at all, the check is equivalent to: the answer must contain
zero dinar amounts (DT, TND, dinars, دينار). The answer must also contain an explicit
"I cannot provide an exact amount" formula.
The script exits with code 1 if a check fails or is inconclusive.

Usage (from the repo root):
    python scripts/test_job_agent.py
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

from agents.education_work.job_agent import (  # noqa: E402
    KB_FILE,
    job_agent,
    load_job_knowledge,
)

SMIG_QUESTION = "Quel est le montant exact du salaire minimum en Tunisie ?"

QUESTIONS = [
    "Comment rédiger un bon CV ?",
    "Comment se préparer à un entretien d'embauche ?",
    # Legal amount: must refuse to give a figure, never invent a dinar amount.
    SMIG_QUESTION,
    # Off-topic: must decline without searching.
    "Quelle heure est-il ?",
]

# Voyage free tier without a payment method: 3 requests/minute, shared by indexing and
# knowledge searches. 21s between requests stays under it. Set to 0 once billing is added.
VOYAGE_PACING_SECONDS = 21

# Dinar amounts, including ranges: "25 DT", "12,5 dinars", "20 à 40 DT", "entre 20 et 40 TND".
PRICE_PATTERN = re.compile(
    r"(?<![\d.,])(\d+(?:[.,]\d+)?)(?:\s*(?:à|-|–|et)\s*(\d+(?:[.,]\d+)?))?\\s*(?:DT|TND|dinars?|د\.?ت|دينار)",
    re.IGNORECASE,
)

# An answer about a legal amount must contain at least one of these.
UNCERTAINTY_PATTERN = re.compile(
    r"(?:ne\s+(?:peux|peut|suis)\s+pas|n[''`]ai\s+pas\s+(?:accès|d[''`]information)|pas\s+en\s+mesure"
    r"|révisé\s+périodiquement|ne\s+figure\s+pas\s+dans\s+ma\s+base"
    r"|ne\s+peux\s+pas\s+vous\s+donner\s+un\s+chiffre"
    r"|chiffre\s+(?:exact|précis)|montant\s+exact|impossible\s+de\s+(?:savoir|vous\s+dire)"
    r"|je\s+ne\s+sais\s+pas|pas\s+dans\s+ma\s+base)",
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
    offenders = [spelling for key, spelling in find_prices(answer).items() if key not in allowed]
    if not UNCERTAINTY_PATTERN.search(answer):
        offenders.append("aucune formule d'incertitude sur le montant légal")
    return offenders


# Regression checks: question -> (label of what is checked, function returning offending strings).
REGRESSION_CHECKS: dict[str, tuple[str, Callable[[str], list[str]]]] = {
    SMIG_QUESTION: ("montant inventé ou refus manquant", ungrounded_prices),
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
    embedded = load_job_knowledge(delay_seconds=VOYAGE_PACING_SECONDS)
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
        response = job_agent.run(question)
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
