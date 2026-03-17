"""Tests for the toxicity filter guardrail."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.settings import get_settings


@pytest.fixture(autouse=True)
def _mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy-key")


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield  # type: ignore[misc]
    get_settings.cache_clear()


def _make_runner_result(output_text: str) -> MagicMock:
    """Create a mock Runner.run result with final_output."""
    result = MagicMock()
    result.final_output = output_text
    return result


class TestToxicityGuardrail:
    @pytest.mark.asyncio
    async def test_clean_input_passes(self) -> None:
        from app.guardrails.input.toxicity_filter import toxicity_guardrail

        llm_response = json.dumps({"is_toxic": False, "reason": "normal query"})

        with patch(
            "app.guardrails.input.toxicity_filter.Runner.run",
            new_callable=AsyncMock,
            return_value=_make_runner_result(llm_response),
        ):
            result = await toxicity_guardrail.guardrail_function(
                MagicMock(), MagicMock(), "Find me Python courses"
            )

        assert result.tripwire_triggered is False
        assert result.output_info["toxicity_detected"] is False

    @pytest.mark.asyncio
    async def test_toxic_input_blocked(self) -> None:
        from app.guardrails.input.toxicity_filter import toxicity_guardrail

        llm_response = json.dumps({"is_toxic": True, "reason": "hate speech detected"})

        with patch(
            "app.guardrails.input.toxicity_filter.Runner.run",
            new_callable=AsyncMock,
            return_value=_make_runner_result(llm_response),
        ):
            result = await toxicity_guardrail.guardrail_function(
                MagicMock(), MagicMock(), "I will kill all of you"
            )

        assert result.tripwire_triggered is True
        assert result.output_info["toxicity_detected"] is True
        assert result.output_info["reason"] == "hate speech detected"

    @pytest.mark.asyncio
    async def test_empty_input_passes(self) -> None:
        from app.guardrails.input.toxicity_filter import toxicity_guardrail

        result = await toxicity_guardrail.guardrail_function(MagicMock(), MagicMock(), "")

        assert result.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_malformed_llm_response_passes(self) -> None:
        """Fail-open: if LLM returns non-JSON, default to not triggered."""
        from app.guardrails.input.toxicity_filter import toxicity_guardrail

        with patch(
            "app.guardrails.input.toxicity_filter.Runner.run",
            new_callable=AsyncMock,
            return_value=_make_runner_result("I cannot determine this"),
        ):
            result = await toxicity_guardrail.guardrail_function(
                MagicMock(), MagicMock(), "some input"
            )

        assert result.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_runner_error_passes(self) -> None:
        """Fail-open: if Runner raises, default to not triggered."""
        from app.guardrails.input.toxicity_filter import toxicity_guardrail

        with patch(
            "app.guardrails.input.toxicity_filter.Runner.run",
            new_callable=AsyncMock,
            side_effect=RuntimeError("LLM unavailable"),
        ):
            result = await toxicity_guardrail.guardrail_function(
                MagicMock(), MagicMock(), "some input"
            )

        assert result.tripwire_triggered is False


class TestToxicityPrompt:
    def test_prompt_file_exists(self) -> None:
        prompt_path = (
            Path(__file__).parent.parent.parent.parent
            / "app"
            / "prompts"
            / "guardrails"
            / "toxicity.md"
        )
        assert prompt_path.exists()
        assert prompt_path.read_text().strip() != ""
