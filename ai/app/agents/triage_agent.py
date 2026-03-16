"""Triage Agent: classifies user intent and routes to specialist agents."""

from __future__ import annotations

from pathlib import Path

from agents import Agent

from app.agents.search_agent import create_search_agent
from app.config.settings import get_settings
from app.guardrails.input.injection_detector import injection_guardrail
from app.guardrails.input.offtopic_detector import offtopic_guardrail
from app.guardrails.input.toxicity_filter import toxicity_guardrail
from app.guardrails.output.hallucination_checker import hallucination_guardrail

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "triage.md"


def create_triage_agent() -> Agent:
    """Create the Triage Agent with handoffs and guardrails."""
    settings = get_settings()
    instructions = _PROMPT_PATH.read_text(encoding="utf-8")
    search_agent = create_search_agent()

    return Agent(
        name="Triage Agent",
        instructions=instructions,
        handoffs=[search_agent],
        input_guardrails=[injection_guardrail, toxicity_guardrail, offtopic_guardrail],
        output_guardrails=[hallucination_guardrail],
        model=settings.AGENT_MODEL,
    )
