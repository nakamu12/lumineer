"""Path Agent: learning path generation specialist."""

from __future__ import annotations

from pathlib import Path

from agents import Agent

from app.config.settings import get_settings
from app.tools.generate_learning_path import generate_learning_path

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "path.md"


def create_path_agent() -> Agent:
    """Create the Path Agent with generate_learning_path tool."""
    settings = get_settings()
    instructions = _PROMPT_PATH.read_text(encoding="utf-8")

    return Agent(
        name="Path Agent",
        handoff_description=(
            "Specialist agent for creating structured learning paths and study plans"
        ),
        instructions=instructions,
        tools=[generate_learning_path],
        model=settings.AGENT_MODEL,
    )
