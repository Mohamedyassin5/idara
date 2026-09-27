"""
Parking Agent — Smoke Test
==========================

Runs parking_agent in isolation (without the hub or orchestrator) on a few
questions and prints the answers plus the tools it called.

Two questions carry an automatic regression check (code, not a second model call):
- the availability question must contain an explicit "I cannot know" formula, and must not
  assert or deny that a place is free (see the heuristic's limits in check_availability);
- the price question must not contain any dinar amount that is absent from parking_kb.md.
The script exits with code 1 if a check fails or is inconclusive.

Usage (from the repo root):
    python scripts/test_parking_agent.py
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

from agents.mobility_city.parking_agent import (  # noqa: E402
    KB_FILE,
    load_parking_knowledge,
    parking_agent,
)

AVAILABILITY_QUESTION = "Y a-t-il de la place pour se garer avenue Habib Bourguiba maintenant ?"
PRICE_QUESTION = "Combien coûte le stationnement au centre-ville ?"

QUESTIONS = [
    "Comment fonctionne le stationnement payant en Tunisie ?",
    # Real-time data: must refuse to state availability, without inventing an answer.
    AVAILABILITY_QUESTION,
    # Must give the indicative range from the knowledge base, never an invented exact price.
    PRICE_QUESTION,
    # Off-topic: must decline without searching.
    "Quelle heure est-il ?",
]

# Voyage free tier without a payment method: 3 requests/minute, shared by indexing and
# knowledge searches. 21s between requests stays under it. Set to 0 once billing is added.
VOYAGE_PACING_SECONDS = 21

# Dinar amounts, including ranges: "25 DT", "12,5 dinars", "1 à 3 DT", "entre 5 et 15 TND", "5-15 DT".
PRICE_PATTERN = re.compile(
    r"(?<![\d.,])(\d+(?:[.,]\d+)?)(?:\s*(?:à|-|–|et)\s*(\d+(?:[.,]\d+)?))?\s*(?:DT|TND|dinars?|د\.?ت|دينار)",
    re.IGNORECASE,
)

# An answer about availability must contain at least one of these.
UNCERTAINTY_PATTERN = re.compile(
    r"(?:ne\s+(?:peux|peut|suis)\s+pas|n['’]ai\s+pas\s+(?:accès|d['’]information)|pas\s+en\s+mesure"
    r"|temps\s+réel|impossible\s+de\s+(?:savoir|vous\s+dire)|je\s+ne\s+sais\s+pas"
    r"|pas\s+dans\s+ma\s+base)",
    re.IGNORECASE,
)

# Claims that a spot is free or full. Each hit is kept only when no hedge precedes it (see
# check_availability), because "je ne peux pas savoir s'il y a de la place" is a correct answer.
AVAILABILITY_CLAIM_PATTERN = re.compile(
    r"(?:il\s+y\s+a\s+(?:de\s+la\s+place|des\s+places|actuellement)|il\s+n['’]y\s+a\s+(?:pas\s+de|plus\s+de)\s+place"
    r"|des\s+places\s+(?:sont|restent)\s+disponibles|aucune\s+place\s+(?:n['’]est\s+)?disponible"
    r"|c['’]est\s+complet|est\s+complet|est\s+plein|vous\s+trouverez\s+(?:facilement\s+)?(?:une\s+place|de\s+la\s+place)"
    r"|vous\s+ne\s+trouverez\s+pas)",
    re.IGNORECASE,
)

# Words that turn a claim into a hedge when they appear shortly before it.
HEDGE_PATTERN = re.compile(
    r"(?:ne\s+(?:peux|peut|sais|saurais)|n['’]ai\s+pas|impossible|savoir|dire|vérifier|si\b|s['’]il"
    r"|pas\s+en\s+mesure|indiquer|garantir|confirmer)",
    re.IGNORECASE,
)
HEDGE_WINDOW = 60  # characters looked at before a claim


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


def check_price(answer: str) -> list[str]:
    """Offending strings for the price question."""
    return ungrounded_prices(answer)


def check_availability(answer: str) -> list[str]:
    """Offending strings for the availability question.

    Two conditions: the answer must say it cannot know, and must not claim a spot is free or
    full. The claim detection is a heuristic: a claim is ignored when a hedging word appears in
    the 60 characters before it, so "je ne peux pas savoir s'il y a de la place" passes. A claim
    phrased differently from the patterns above will not be caught — the mandatory uncertainty
    formula is the reliable half of this check.
    """
    offenders = []
    if not UNCERTAINTY_PATTERN.search(answer):
        offenders.append("aucune formule d'incertitude (« je ne peux pas savoir », « temps réel »…)")
    for match in AVAILABILITY_CLAIM_PATTERN.finditer(answer):
        context = answer[max(0, match.start() - HEDGE_WINDOW) : match.start()]
        if not HEDGE_PATTERN.search(context):
            offenders.append(f"affirmation de disponibilité : « {match.group(0)} »")
    return offenders


# Regression checks: question -> (label of what is checked, function returning offending strings).
REGRESSION_CHECKS: dict[str, tuple[str, Callable[[str], list[str]]]] = {
    AVAILABILITY_QUESTION: ("disponibilité affirmée ou refus manquant", check_availability),
    PRICE_QUESTION: ("prix absent de la base", check_price),
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
    embedded = load_parking_knowledge(delay_seconds=VOYAGE_PACING_SECONDS)
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
        response = parking_agent.run(question)
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
