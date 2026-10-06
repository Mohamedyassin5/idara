"""
Routing Eval Cases
==================

Each case sends one question to the Master Orchestrator and states which FINAL agent must answer it
(orchestrator -> hub -> agent). The runner (evals/__main__.py) reads the agent that actually produced
the answer from the nested `member_responses` of the run, so the check is structural, not text-based.

Case kinds:
- ``domain``      one clear, typical question per real agent, written without the agent's obvious keyword
                  (tests understanding of the meaning, not lexical overlap).
- ``trap``        deliberately ambiguous: looks like it belongs to another hub/agent but belongs here.
- ``placeholder`` agents that are still stubs (benevolat): routing must reach them, not a real agent.

Add a case below, then run `python -m evals`.
"""

from dataclasses import dataclass

# Final agent id -> hub id it belongs to (mirrors agents/hubs.py).
HUB_OF: dict[str, str] = {
    "bureaucratie-agent": "admin-utilities-hub",
    "steg-agent": "admin-utilities-hub",
    "entrepreneuriat-agent": "admin-utilities-hub",
    "louage-agent": "mobility-city-hub",
    "parking-agent": "mobility-city-hub",
    "souk-agent": "mobility-city-hub",
    "bac-agent": "education-work-hub",
    "job-agent": "education-work-hub",
    "immobilier-agent": "housing-community-hub",
    "benevolat-agent": "housing-community-hub",
}


@dataclass(frozen=True)
class RoutingCase:
    """One question and the single final agent expected to answer it."""

    name: str
    question: str
    expected_agent: str
    kind: str  # "domain" | "trap" | "placeholder"

    @property
    def expected_hub(self) -> str:
        return HUB_OF[self.expected_agent]


CASES: tuple[RoutingCase, ...] = (
    # --- One typical question per real agent -------------------------------------------------
    RoutingCase(
        name="bureaucratie_passeport",
        question="Mon fils de 20 ans n'a jamais voyagé, quelles pièces dois-je réunir pour lui faire son premier document de voyage ?",
        expected_agent="bureaucratie-agent",
        kind="domain",
    ),
    RoutingCase(
        name="steg_facture_electricite",
        question="Le montant de ma facture d'électricité ce mois-ci est bien plus élevé que d'habitude, que puis-je faire pour la contester ?",
        expected_agent="steg-agent",
        kind="domain",
    ),
    RoutingCase(
        name="entrepreneuriat_statut_independant",
        question="Je voudrais lancer mon activité de graphiste en indépendant, quelle forme juridique dois-je choisir pour démarrer ?",
        expected_agent="entrepreneuriat-agent",
        kind="domain",
    ),
    RoutingCase(
        name="louage_sfax_gabes",
        question="Je dois aller de Sfax à Gabès demain matin en transport collectif, où je peux embarquer et à peu près combien ça coûte ?",
        expected_agent="louage-agent",
        kind="domain",
    ),
    RoutingCase(
        name="parking_paiement_centre_ville",
        question="Je me gare souvent en centre-ville, comment régler mon temps de stationnement dans la rue ?",
        expected_agent="parking-agent",
        kind="domain",
    ),
    RoutingCase(
        name="souk_negociation_tapis",
        question="Je veux acheter un tapis dans la médina, comment marchander pour ne pas payer le prix touriste ?",
        expected_agent="souk-agent",
        kind="domain",
    ),
    RoutingCase(
        name="bac_calcul_moyenne",
        question="Ma fille passe ses examens de fin de lycée en juin, comment sa note finale est-elle calculée ?",
        expected_agent="bac-agent",
        kind="domain",
    ),
    RoutingCase(
        name="job_presenter_candidature",
        question="Je viens d'obtenir mon diplôme d'ingénieur, comment structurer ma candidature pour qu'un recruteur me rappelle ?",
        expected_agent="job-agent",
        kind="domain",
    ),
    RoutingCase(
        name="immobilier_eviter_arnaque",
        question="Je cherche un appartement à louer à Sousse, comment repérer les annonces qui cachent une arnaque ?",
        expected_agent="immobilier-agent",
        kind="domain",
    ),
    # --- Intentional traps -------------------------------------------------------------------
    RoutingCase(
        name="trap_carte_grise_vs_mobility",
        question="J'ai acheté une voiture d'occasion la semaine dernière, comment la mettre à mon nom auprès de l'administration ?",
        expected_agent="bureaucratie-agent",  # looks like mobility, is a vehicle registration (carte grise)
        kind="trap",
    ),
    RoutingCase(
        name="trap_prix_trajet_vs_souk",
        question="Combien je dois compter pour un trajet de Tunis à Sousse, et est-ce que le prix se discute ?",
        expected_agent="louage-agent",  # "prix qui se discute" looks like souk, is a transport fare
        kind="trap",
    ),
    RoutingCase(
        name="trap_fourriere_vs_bureaucratie",
        question="Ma voiture a disparu de la rue où je l'avais laissée hier, je crois qu'elle a été embarquée, comment la récupérer ?",
        expected_agent="parking-agent",  # looks like an administrative/police matter, is a fourrière question
        kind="trap",
    ),
    # --- Placeholder agents ------------------------------------------------------------------
    RoutingCase(
        name="placeholder_benevolat_aide",
        question="J'ai du temps libre le week-end et je voudrais aider des personnes âgées de mon quartier, comment m'engager ?",
        expected_agent="benevolat-agent",
        kind="placeholder",
    ),
)
