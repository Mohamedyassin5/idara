"""
Kotob Agent
===========

Placeholder — hub: education_work, domaine: kotob (livres scolaires).
"""

from agno.agent import Agent

from app.settings import chat_model

INSTRUCTIONS = """\
Tu es un agent placeholder pour le domaine livres scolaires.
Quelle que soit la demande, réponds seulement :
'Ce module n'est pas encore implémenté - hub: education_work, domaine: kotob'
"""

kotob_agent = Agent(
    id="kotob-agent",
    name="Kotob Agent",
    role="Livres et fournitures scolaires : disponibilité, échange, achat",
    model=chat_model(),
    instructions=INSTRUCTIONS,
    markdown=True,
)
