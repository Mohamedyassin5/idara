"""
Benevolat Agent
===============

Placeholder — hub: housing_community, domaine: benevolat (bénévolat et associations).
"""

from agno.agent import Agent

from app.settings import chat_model

INSTRUCTIONS = """\
Tu es un agent placeholder pour le domaine bénévolat/associations.
Quelle que soit la demande, réponds seulement :
'Ce module n'est pas encore implémenté - hub: housing_community, domaine: benevolat'
"""

benevolat_agent = Agent(
    id="benevolat-agent",
    name="Benevolat Agent",
    role="Bénévolat, associations et initiatives citoyennes",
    model=chat_model(),
    instructions=INSTRUCTIONS,
    markdown=True,
)
