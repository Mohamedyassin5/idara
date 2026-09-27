"""
Hubs
====

The four domain hubs. Each hub is a Team that routes a request to the single
domain agent best suited to answer it (Team of Teams: the Master Orchestrator
has these hubs as members).
"""

from agno.team import Team

from agents.admin_utilities.bureaucratie_agent import bureaucratie_agent
from agents.admin_utilities.entrepreneuriat_agent import entrepreneuriat_agent
from agents.admin_utilities.steg_agent import steg_agent
from agents.education_work.bac_agent import bac_agent
from agents.education_work.job_agent import job_agent
from agents.education_work.kotob_agent import kotob_agent
from agents.housing_community.benevolat_agent import benevolat_agent
from agents.housing_community.immobilier_agent import immobilier_agent
from agents.mobility_city.louage_agent import louage_agent
from agents.mobility_city.parking_agent import parking_agent
from agents.mobility_city.souk_agent import souk_agent
from app.settings import chat_model

HUB_INSTRUCTIONS = """\
Tu es le hub {hub}. Transmets la demande de l'utilisateur à l'unique agent membre
dont le domaine correspond le mieux, et renvoie sa réponse telle quelle.
Ne réponds jamais toi-même sur le fond.
"""

# ---------------------------------------------------------------------------
# Admin & Utilities — bureaucratie, STEG/SONEDE
# ---------------------------------------------------------------------------
admin_utilities_hub = Team(
    id="admin-utilities-hub",
    name="Admin & Utilities Hub",
    role="Démarches administratives, papiers, STEG (électricité/gaz) et SONEDE (eau)",
    model=chat_model(),
    members=[bureaucratie_agent, steg_agent, entrepreneuriat_agent],
    instructions=HUB_INSTRUCTIONS.format(hub="admin_utilities"),
    respond_directly=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Mobility & City — louage/transport, parking/trafic, marché/souk
# ---------------------------------------------------------------------------
mobility_city_hub = Team(
    id="mobility-city-hub",
    name="Mobility & City Hub",
    role="Transport et louage, parking et trafic, marchés et souks",
    model=chat_model(),
    members=[louage_agent, parking_agent, souk_agent],
    instructions=HUB_INSTRUCTIONS.format(hub="mobility_city"),
    respond_directly=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Education & Work — bac/concours, emploi, livres scolaires
# ---------------------------------------------------------------------------
education_work_hub = Team(
    id="education-work-hub",
    name="Education & Work Hub",
    role="Bac et concours, recherche d'emploi, livres scolaires",
    model=chat_model(),
    members=[bac_agent, job_agent, kotob_agent],
    instructions=HUB_INSTRUCTIONS.format(hub="education_work"),
    respond_directly=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Housing & Community — immobilier, bénévolat/associations
# ---------------------------------------------------------------------------
housing_community_hub = Team(
    id="housing-community-hub",
    name="Housing & Community Hub",
    role="Immobilier (location, achat), bénévolat et associations",
    model=chat_model(),
    members=[immobilier_agent, benevolat_agent],
    instructions=HUB_INSTRUCTIONS.format(hub="housing_community"),
    respond_directly=True,
    markdown=True,
)

HUBS = [admin_utilities_hub, mobility_city_hub, education_work_hub, housing_community_hub]
