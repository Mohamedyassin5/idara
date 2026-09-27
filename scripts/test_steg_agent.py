"""
STEG Agent — Smoke Test
=======================

Runs steg_agent in isolation (without the hub or orchestrator) on a few
questions and prints the answers plus the tools it called.

Some questions carry an automatic regression check: the answer must not contain any
forbidden term. The script exits with code 1 if a check fails or is inconclusive.

Usage (from the repo root):
    python scripts/test_steg_agent.py
"""

import sys
import time
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evals.dotenv import load_dotenv  # noqa: E402

# Keys must be in os.environ before the model and embedder clients are built.
load_dotenv()

from agents.admin_utilities.steg_agent import (  # noqa: E402
    load_steg_knowledge,
    steg_agent,
)

COMPLAINT_QUESTION = (
    "La STEG m'a coupé l'électricité alors que j'avais payé ma facture, et l'agence refuse de régler le problème. "
    "Auprès de quel organisme je peux porter plainte contre la STEG ?"
)

QUESTIONS = [
    "Comment payer ma facture STEG en ligne ?",
    "Je trouve ma facture trop élevée, comment la contester ?",
    "Comment résilier un ancien abonnement STEG ?",
    # Pushes outside the knowledge base: must not name any recourse body (rule 3).
    COMPLAINT_QUESTION,
    # Off-topic: must decline without searching.
    "Quelle heure est-il ?",
]

# Regression checks: question -> terms that must never appear in the answer.
# Matching ignores case and accents ("Médiateur", "mediateur" and "MÉDIATEUR" all match).
FORBIDDEN_TERMS = {
    COMPLAINT_QUESTION: [
        "médiateur",
        "INRSE",
        "instance de régulation",
        "commission de protection",
        "tribunal",
        "ministère",
    ],
}

# Voyage free tier without a payment method: 3 requests/minute, shared by indexing and
# knowledge searches. 21s between requests stays under it. Set to 0 once billing is added.
VOYAGE_PACING_SECONDS = 21


def normalize(text: str) -> str:
    """Casefold and strip accents so matching is case- and accent-insensitive."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def check_forbidden_terms(answer: str, tools: list[str], terms: list[str]) -> bool:
    """Print a pass/fail verdict for one answer. Returns True on pass."""
    # A run that errored (rate limit, API error) returns the error text as content and calls
    # no tool: it contains no forbidden term but proves nothing, so it must not count as a pass.
    if not answer.strip() or "search_knowledge_base" not in tools:
        print("❌ NON CONCLUANT : réponse vide ou aucune recherche dans la base (erreur API ou quota ?)")
        return False
    normalized_answer = normalize(answer)
    found = [term for term in terms if normalize(term) in normalized_answer]
    if found:
        print(f"❌ RÉGRESSION : nom interdit trouvé : {', '.join(found)}")
        return False
    print("✅ Aucun nom interdit dans la réponse")
    return True


def main() -> None:
    # Windows consoles default to cp1252; force UTF-8 so accents, emoji and Arabic script print.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("Chargement de la base de connaissances…")
    embedded = load_steg_knowledge(delay_seconds=VOYAGE_PACING_SECONDS)
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
        response = steg_agent.run(question)
        answer = response.content if isinstance(response.content, str) else str(response.content or "")
        print(answer)
        tools = [tool.tool_name for tool in (response.tools or [])]
        print(f"\n(outils appelés : {', '.join(tools) if tools else 'aucun'})")

        if question in FORBIDDEN_TERMS:
            print()
            if not check_forbidden_terms(answer, tools, FORBIDDEN_TERMS[question]):
                failed_checks.append(f"[{i}] {question}")

    checked = sum(1 for question in QUESTIONS if question in FORBIDDEN_TERMS)
    print("\n" + "=" * 80)
    if failed_checks:
        print(f"❌ {len(failed_checks)}/{checked} test(s) de régression en échec :")
        for failure in failed_checks:
            print(f"   - {failure}")
        sys.exit(1)
    print(f"✅ {checked}/{checked} test(s) de régression réussi(s)")


if __name__ == "__main__":
    main()
