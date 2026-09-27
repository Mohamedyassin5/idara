"""
Master Orchestrator
===================

Top-level Team. Routes every user request to one of the four hubs, which in
turn route it to a domain agent. Sessions and memory are persisted here (the
top-level team owns the session for the whole tree).
"""

from agno.team import Team

from agents.hubs import HUBS
from app.settings import chat_model
from db import get_db

INSTRUCTIONS = """\
Tu es le Master Orchestrator d'une super-app d'assistance à la vie quotidienne en Tunisie.
Analyse la demande de l'utilisateur et transmets-la au hub le plus pertinent :
- Admin & Utilities Hub : papiers, démarches administratives, STEG, SONEDE.
- Mobility & City Hub : transport, louage, parking, trafic, marchés, souks.
- Education & Work Hub : bac, concours, emploi, livres scolaires.
- Housing & Community Hub : immobilier, bénévolat, associations.
Renvoie la réponse du hub telle quelle. Si aucune catégorie ne correspond, demande une précision à l'utilisateur.
"""

master_orchestrator = Team(
    id="master-orchestrator",
    name="Master Orchestrator",
    model=chat_model(),
    db=get_db(),
    members=HUBS,
    instructions=INSTRUCTIONS,
    respond_directly=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
)
