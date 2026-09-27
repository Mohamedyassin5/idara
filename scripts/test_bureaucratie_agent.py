"""
Bureaucratie Agent — Smoke Test
===============================

Runs bureaucratie_agent in isolation (without the hub or orchestrator) on a few
questions and prints the answers plus the tools it called.

Usage (from the repo root):
    uv run python scripts/test_bureaucratie_agent.py
"""

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evals.dotenv import load_dotenv  # noqa: E402

# Keys must be in os.environ before the model and embedder clients are built.
load_dotenv()

from agents.admin_utilities.bureaucratie_agent import (  # noqa: E402
    bureaucratie_agent,
    load_bureaucratie_knowledge,
)

QUESTIONS = [
    "Quels documents faut-il pour renouveler ma carte d'identité nationale ?",
    "Je viens de créer ma société, comment déclarer mon premier employé à la CNSS ?",
    # In scope but absent from the knowledge base: must say so instead of inventing.
    "Quels papiers faut-il pour un acte de mariage à la mairie ?",
    # Tunisian dialect (arabizi): must answer in derja.
    "chnowa lazem bech na3mel passeport lawel marra ?",
    # Off-topic: must decline without searching.
    "Quelle heure est-il ?",
]

# Voyage free tier without a payment method: 3 requests/minute, shared by indexing and
# knowledge searches. 21s between requests stays under it. Set to 0 once billing is added.
VOYAGE_PACING_SECONDS = 21


def main() -> None:
    # Windows consoles default to cp1252; force UTF-8 so accents and Arabic script print.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("Chargement de la base de connaissances…")
    embedded = load_bureaucratie_knowledge(delay_seconds=VOYAGE_PACING_SECONDS)
    print(f"{embedded} section(s) envoyée(s) à l'indexation.")
    if embedded and VOYAGE_PACING_SECONDS:
        print("Pause de 60s pour laisser se vider le quota Voyage avant les recherches…")
        time.sleep(60)

    for i, question in enumerate(QUESTIONS, start=1):
        if i > 1 and VOYAGE_PACING_SECONDS:
            time.sleep(VOYAGE_PACING_SECONDS)
        print("\n" + "=" * 80)
        print(f"[{i}/{len(QUESTIONS)}] {question}")
        print("-" * 80)
        response = bureaucratie_agent.run(question)
        print(response.content)
        tools = [tool.tool_name for tool in (response.tools or [])]
        print(f"\n(outils appelés : {', '.join(tools) if tools else 'aucun'})")


if __name__ == "__main__":
    main()
