"""Search Agent: course discovery specialist."""

from __future__ import annotations

from pathlib import Path

from agents import Agent

from app.config.settings import get_settings
from app.tools.search_courses import search_courses

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "search.md"


def create_search_agent() -> Agent:
    """Create the Search Agent with search_courses tool."""
    settings = get_settings()
    instructions = _PROMPT_PATH.read_text(encoding="utf-8")

    return Agent(
        name="Search Agent",
        handoff_description="Specialist agent for course search and discovery",
        instructions=instructions,
        tools=[search_courses],
        model=settings.AGENT_MODEL,
    )
