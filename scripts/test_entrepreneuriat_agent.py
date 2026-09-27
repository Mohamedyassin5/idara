"""
Entrepreneuriat Agent — Smoke Test
==================================

Runs entrepreneuriat_agent in isolation (without the hub or orchestrator) on a few
questions and prints the answers plus the tools it called.

Automatic regression check on question 1 (vague project):
- The answer must contain a question mark (clarification question asked).
- The answer must NOT contain "RNE" or "matricule fiscal" (no premature detailed checklist).

Usage (from the repo root):
    python scripts/test_entrepreneuriat_agent.py
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

from agents.admin_utilities.entrepreneuriat_agent import (  # noqa: E402
    entrepreneuriat_agent,
    load_entrepreneuriat_knowledge,
)

VAGUE_QUESTION = "Je veux monter une entreprise, comment je fais ?"

QUESTIONS = [
    # Vague question: must ask a clarification question without premature checklist (RNE, matricule fiscal).
    VAGUE_QUESTION,
    # Specific question: should give a checklist (legal form, RNE, matricule fiscal, sanitary authorizations).
    "Je veux ouvrir un café, quelles sont les démarches administratives ?",
    # Specific question about exact minimum capital: must refuse an exact figure and explain it.
    "Quel est le montant exact du capital minimum pour une SARL ?",
    # Off-topic: must decline without searching.
    "Quelle heure est-il ?",
]

# Voyage free tier without a payment method: 3 requests/minute, shared by indexing and
# knowledge searches. 21s between requests stays under it. Set to 0 once billing is added.
VOYAGE_PACING_SECONDS = 21


# Heuristique imparfaite : détecte une demande de clarification soit par un point
# d'interrogation littéral (« ? »), soit par des tournures interrogatives ou d'invitation
# à préciser courantes en français, même terminées par deux-points ou sans « ? » explicite
# (ex. « pourriez-vous », « pouvez-vous », « quel est », « quelle est », « quels sont », « quelles sont »).
CLARIFICATION_PATTERN = re.compile(
    r"(?:\?|pourriez[- ]vous|pouvez[- ]vous|quel(?:le)?s?\s+(?:est|sont)|merci\s+de\s+(?:pr[eé]ciser|m['’]indiquer))",
    re.IGNORECASE,
)


def check_clarification(answer: str) -> list[str]:
    """Check that the answer to a vague question asks for clarification without prematurely giving RNE/matricule fiscal."""
    offenders: list[str] = []
    if not CLARIFICATION_PATTERN.search(answer):
        offenders.append("aucune question ou demande de clarification détectée (ni '?', ni formule interrogative)")
    if re.search(r"\bRNE\b", answer, re.IGNORECASE):
        offenders.append("mention prématurée du mot « RNE »")
    if re.search(r"matricule\s+fiscal", answer, re.IGNORECASE):
        offenders.append("mention prématurée des mots « matricule fiscal »")
    return offenders


REGRESSION_CHECKS: dict[str, tuple[str, Callable[[str], list[str]]]] = {
    VAGUE_QUESTION: ("clarification demandée sans checklist prématurée", check_clarification),
}


def run_check(answer: str, tools: list[str], label: str, find_offenders: Callable[[str], list[str]]) -> bool:
    """Print a pass/fail verdict for one answer. Returns True on pass."""
    if not answer.strip():
        print("❌ NON CONCLUANT : réponse vide")
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
    embedded = load_entrepreneuriat_knowledge(delay_seconds=VOYAGE_PACING_SECONDS)
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
        response = entrepreneuriat_agent.run(question)
        answer = response.content if isinstance(response.content, str) else str(response.content or "")
        print(answer)
        tools = [tool.tool_name for tool in (response.tools or [])]
        print(f"\n(outils appelés : {', '.join(tools) if tools else 'aucun'})")

        if question in REGRESSION_CHECKS:
            print()
            label, find_offenders = REGRESSION_CHECKS[question]
            if not run_check(answer, tools, label, find_offenders):
                failed_checks.append(f"[{i}] {question}")

    checked = len(REGRESSION_CHECKS)
    print("\n" + "=" * 80)
    if failed_checks:
        print(f"❌ {len(failed_checks)}/{checked} test(s) de régression en échec :")
        for failure in failed_checks:
            print(f"   - {failure}")
        sys.exit(1)
    print(f"✅ {checked}/{checked} test(s) de régression réussi(s)")


if __name__ == "__main__":
    main()
