"""
Direct Chat
===========

POST /chat/{agent_id}/run — runs one domain agent directly, skipping the orchestrator and hub.
Those two routing calls cost two extra model round trips per question, and a domain page already
knows which agent it talks to. The sessions are stored under the agent itself (type "agent").
"""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException

from agents.admin_utilities.bureaucratie_agent import bureaucratie_agent
from agents.admin_utilities.entrepreneuriat_agent import entrepreneuriat_agent
from agents.admin_utilities.steg_agent import steg_agent
from agents.education_work.bac_agent import bac_agent
from agents.education_work.job_agent import job_agent
from agents.housing_community.immobilier_agent import immobilier_agent
from agents.mobility_city.louage_agent import louage_agent
from agents.mobility_city.parking_agent import parking_agent
from agents.mobility_city.souk_agent import souk_agent
from db import get_db

router = APIRouter(prefix="/chat", tags=["Chat"])

# Copies, so the instances shared with the hubs keep running without storage of their own.
_AGENTS = {
    agent.id: agent.deep_copy(update={"db": get_db(), "add_history_to_context": True, "num_history_runs": 5})
    for agent in (
        bureaucratie_agent,
        steg_agent,
        entrepreneuriat_agent,
        louage_agent,
        parking_agent,
        souk_agent,
        bac_agent,
        job_agent,
        immobilier_agent,
    )
}


@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: str,
    message: Annotated[str, Form()],
    session_id: Annotated[str, Form()],
    user_id: Annotated[str, Form()],
) -> dict:
    agent = _AGENTS.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")
    run = await agent.arun(message, session_id=session_id, user_id=user_id)
    return {"agent_id": agent_id, "content": run.content if isinstance(run.content, str) else str(run.content or "")}
