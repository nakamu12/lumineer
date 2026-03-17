"""Tests for the off-topic detector guardrail."""

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


class TestOfftopicGuardrail:
    @pytest.mark.asyncio
    async def test_course_query_passes(self) -> None:
        from app.guardrails.input.offtopic_detector import offtopic_guardrail

        llm_response = json.dumps({"is_offtopic": False, "reason": "course search"})

        with patch(
            "app.guardrails.input.offtopic_detector.Runner.run",
            new_callable=AsyncMock,
            return_value=_make_runner_result(llm_response),
        ):
            result = await offtopic_guardrail.guardrail_function(
                MagicMock(), MagicMock(), "Find me Python courses"
            )

        assert result.tripwire_triggered is False
        assert result.output_info["offtopic_detected"] is False

    @pytest.mark.asyncio
    async def test_offtopic_input_blocked(self) -> None:
        from app.guardrails.input.offtopic_detector import offtopic_guardrail

        llm_response = json.dumps({"is_offtopic": True, "reason": "weather question"})

        with patch(
            "app.guardrails.input.offtopic_detector.Runner.run",
            new_callable=AsyncMock,
            return_value=_make_runner_result(llm_response),
        ):
            result = await offtopic_guardrail.guardrail_function(
                MagicMock(), MagicMock(), "What is the weather today?"
            )

        assert result.tripwire_triggered is True
        assert result.output_info["offtopic_detected"] is True

    @pytest.mark.asyncio
    async def test_grey_zone_career_question_passes(self) -> None:
        from app.guardrails.input.offtopic_detector import offtopic_guardrail

        llm_response = json.dumps(
            {"is_offtopic": False, "reason": "career-related, grey-zone allowed"}
        )

        with patch(
            "app.guardrails.input.offtopic_detector.Runner.run",
            new_callable=AsyncMock,
            return_value=_make_runner_result(llm_response),
        ):
            result = await offtopic_guardrail.guardrail_function(
                MagicMock(), MagicMock(), "Is a data science degree worth it?"
            )

        assert result.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_empty_input_passes(self) -> None:
        from app.guardrails.input.offtopic_detector import offtopic_guardrail

        result = await offtopic_guardrail.guardrail_function(MagicMock(), MagicMock(), "")

        assert result.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_malformed_llm_response_passes(self) -> None:
        from app.guardrails.input.offtopic_detector import offtopic_guardrail

        with patch(
            "app.guardrails.input.offtopic_detector.Runner.run",
            new_callable=AsyncMock,
            return_value=_make_runner_result("not valid json"),
        ):
            result = await offtopic_guardrail.guardrail_function(
                MagicMock(), MagicMock(), "some input"
            )

        assert result.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_runner_error_passes(self) -> None:
        from app.guardrails.input.offtopic_detector import offtopic_guardrail

        with patch(
            "app.guardrails.input.offtopic_detector.Runner.run",
            new_callable=AsyncMock,
            side_effect=RuntimeError("LLM unavailable"),
        ):
            result = await offtopic_guardrail.guardrail_function(
                MagicMock(), MagicMock(), "some input"
            )

        assert result.tripwire_triggered is False


class TestOfftopicPrompt:
    def test_prompt_file_exists(self) -> None:
        prompt_path = (
            Path(__file__).parent.parent.parent.parent
            / "app"
            / "prompts"
            / "guardrails"
            / "offtopic.md"
        )
        assert prompt_path.exists()
        assert prompt_path.read_text().strip() != ""
