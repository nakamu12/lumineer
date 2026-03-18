"""Skill Gap Agent: skill gap analysis specialist."""

from __future__ import annotations

from pathlib import Path

from agents import Agent

from app.config.settings import get_settings
from app.tools.analyze_skill_gap import analyze_skill_gap

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "skill_gap.md"


def create_skill_gap_agent() -> Agent:
    """Create the Skill Gap Agent with analyze_skill_gap tool."""
    settings = get_settings()
    instructions = _PROMPT_PATH.read_text(encoding="utf-8")

    return Agent(
        name="Skill Gap Agent",
        handoff_description=(
            "Specialist agent for analyzing skill gaps between"
            " current skills and target career goals"
        ),
        instructions=instructions,
        tools=[analyze_skill_gap],
        model=settings.AGENT_MODEL,
    )
