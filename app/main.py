"""
AgentOS Entrypoint
==================
"""

import asyncio
from contextlib import asynccontextmanager
from os import getenv
from pathlib import Path

from evals.dotenv import load_dotenv

# Local runs: hydrate os.environ from .env before anything reads it (API keys are read
# at import time, RUNTIME_ENV just below). Existing env vars win, so Docker's env_file is unaffected.
load_dotenv()

from agno.os import AgentOS  # noqa: E402
from agno.utils.log import log_info  # noqa: E402

from agents.admin_utilities.bureaucratie_agent import load_bureaucratie_knowledge  # noqa: E402
from agents.admin_utilities.entrepreneuriat_agent import load_entrepreneuriat_knowledge  # noqa: E402
from agents.admin_utilities.steg_agent import load_steg_knowledge  # noqa: E402
from agents.mobility_city.louage_agent import load_louage_knowledge  # noqa: E402
from agents.mobility_city.parking_agent import load_parking_knowledge  # noqa: E402
from agents.education_work.bac_agent import load_bac_knowledge  # noqa: E402
from agents.education_work.job_agent import load_job_knowledge  # noqa: E402
from agents.housing_community.immobilier_agent import load_immobilier_knowledge  # noqa: E402
from agents.mobility_city.souk_agent import load_souk_knowledge  # noqa: E402
from agents.orchestrator import master_orchestrator  # noqa: E402
from app.auth import auth_middleware, router as auth_router  # noqa: E402
from app.chat import router as chat_router  # noqa: E402
from app.cv import router as cv_router  # noqa: E402
from app.jobs import router as jobs_router  # noqa: E402
from app.whatsapp import router as whatsapp_router  # noqa: E402
from db import get_db  # noqa: E402

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
runtime_env = getenv("RUNTIME_ENV", "prd")
scheduler_base_url = getenv("AGENTOS_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------------------------
# Interfaces
# - The Master Orchestrator becomes available on Slack when both env vars are set
# ---------------------------------------------------------------------------
SLACK_BOT_TOKEN = getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = getenv("SLACK_SIGNING_SECRET", "")

interfaces: list = []
if SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET:
    from agno.os.interfaces.slack import Slack

    interfaces.append(
        Slack(
            team=master_orchestrator,
            streaming=True,
            token=SLACK_BOT_TOKEN,
            signing_secret=SLACK_SIGNING_SECRET,
            resolve_user_identity=True,
        )
    )


async def index_knowledge() -> None:
    """Index the knowledge bases (no-op for sections already indexed).

    Runs in the background: a first indexing can take a while on CPU, and the server must accept
    requests (and pass the hosting platform's startup health check) long before that. Each loader runs in a thread because
    indexing is blocking I/O.
    """
    knowledge_loaders = [
        ("Bureaucratie", load_bureaucratie_knowledge),
        ("STEG", load_steg_knowledge),
        ("Louage", load_louage_knowledge),
        ("Parking", load_parking_knowledge),
        ("Souk", load_souk_knowledge),
        ("Bac", load_bac_knowledge),
        ("Job", load_job_knowledge),
        ("Immobilier", load_immobilier_knowledge),
        ("Entrepreneuriat", load_entrepreneuriat_knowledge),
    ]
    embedded = 0
    for label, load_knowledge in knowledge_loaders:
        try:
            embedded = await asyncio.to_thread(load_knowledge)
            log_info(f"{label} knowledge base ready ({embedded} section(s) indexed)")
        except Exception as exc:  # one failing knowledge base must not stop the others
            embedded = 0
            log_info(f"{label} knowledge base indexing failed: {exc}")


# ---------------------------------------------------------------------------
# Lifespan — extension hook for app-level startup / teardown.
#
# AgentOS handles the MCP lifecycle (connect on startup, close on shutdown).
# Knowledge indexing starts in the background so the server is ready immediately.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app):  # type: ignore[no-untyped-def]
    log_info("AgentOS lifespan: startup")
    indexing = asyncio.create_task(index_knowledge())
    try:
        yield
    finally:
        indexing.cancel()
        log_info("AgentOS lifespan: shutdown")


# ---------------------------------------------------------------------------
# Create AgentOS
# - The Master Orchestrator is the single entry point; hubs and domain agents
#   are reached through it.
# ---------------------------------------------------------------------------
agent_os = AgentOS(
    name="AgentOS",
    tracing=True,
    scheduler=True,
    scheduler_base_url=scheduler_base_url,
    authorization=runtime_env == "prd",
    lifespan=lifespan,
    db=get_db(),
    teams=[master_orchestrator],
    interfaces=interfaces,
    config=str(Path(__file__).parent / "config.yaml"),
)
app = agent_os.get_app()
app.include_router(auth_router)
app.include_router(cv_router)
app.include_router(chat_router)
app.include_router(whatsapp_router)
app.include_router(jobs_router)
app.middleware("http")(auth_middleware)


if __name__ == "__main__":
    agent_os.serve(app="app.main:app", reload=runtime_env == "dev")
