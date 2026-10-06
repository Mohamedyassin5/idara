"""
App Settings
============

Shared runtime objects for the platform.
"""

from os import getenv

from agno.models.openai import OpenAILike, OpenAIResponses


def default_model() -> OpenAIResponses:
    """Fresh model instance per agent — avoids shared-state footguns."""
    return OpenAIResponses(id="gpt-5.4")


def chat_model() -> OpenAILike:
    """Fresh apinex (OpenAI-compatible) instance per agent/team, reading LLM_BASE_URL, LLM_API_KEY, LLM_MODEL."""
    return OpenAILike(
        id=getenv("LLM_MODEL", "claude-sonnet-5"),
        base_url=getenv("LLM_BASE_URL"),
        api_key=getenv("LLM_API_KEY"),
    )
