"""
App Settings
============

Shared runtime objects for the platform.
"""

from agno.models.groq import Groq
from agno.models.openai import OpenAIResponses


def default_model() -> OpenAIResponses:
    """Fresh model instance per agent — avoids shared-state footguns."""
    return OpenAIResponses(id="gpt-5.4")


def chat_model() -> Groq:
    """Fresh Groq instance per agent/team — used by the orchestrator, hubs and domain agents.

    Reads GROQ_API_KEY from the environment.
    """
    return Groq(id="openai/gpt-oss-120b")
