"""Tests for agent creation factories."""

import pytest
from agents import Agent

from app.agents.search_agent import create_search_agent
from app.agents.triage_agent import create_triage_agent


@pytest.fixture(autouse=True)
def _mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure OPENAI_API_KEY is set so Settings can initialize."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy-key")


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """Clear the lru_cache on get_settings so monkeypatched env is picked up."""
    from app.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestCreateSearchAgent:
    def test_returns_agent(self) -> None:
        agent = create_search_agent()
        assert isinstance(agent, Agent)

    def test_name(self) -> None:
        agent = create_search_agent()
        assert agent.name == "Search Agent"

    def test_has_search_tool(self) -> None:
        agent = create_search_agent()
        tool_names = [t.name for t in agent.tools]
        assert "search_courses" in tool_names

    def test_has_handoff_description(self) -> None:
        agent = create_search_agent()
        assert agent.handoff_description is not None
        assert len(agent.handoff_description) > 0

    def test_instructions_loaded_from_file(self) -> None:
        agent = create_search_agent()
        assert "Search Agent" in agent.instructions or "search" in agent.instructions.lower()
        assert len(agent.instructions) > 50


class TestCreateTriageAgent:
    def test_returns_agent(self) -> None:
        agent = create_triage_agent()
        assert isinstance(agent, Agent)

    def test_name(self) -> None:
        agent = create_triage_agent()
        assert agent.name == "Triage Agent"

    def test_has_no_tools(self) -> None:
        agent = create_triage_agent()
        tool_names = [t.name for t in agent.tools]
        assert "search_courses" not in tool_names

    def test_has_handoffs(self) -> None:
        agent = create_triage_agent()
        assert len(agent.handoffs) > 0

    def test_handoff_to_search_agent(self) -> None:
        agent = create_triage_agent()
        # Handoffs are Agent objects directly
        handoff_names = [h.name for h in agent.handoffs]
        assert "Search Agent" in handoff_names

    def test_has_input_guardrails(self) -> None:
        agent = create_triage_agent()
        assert len(agent.input_guardrails) > 0

    def test_has_output_guardrails(self) -> None:
        agent = create_triage_agent()
        assert len(agent.output_guardrails) > 0

    def test_instructions_loaded_from_file(self) -> None:
        agent = create_triage_agent()
        assert "Triage" in agent.instructions or "routing" in agent.instructions.lower()
        assert len(agent.instructions) > 50
