"""Tests for the privacy filter guardrail."""

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


class TestPrivacyPatternDetection:
    """Test Stage 1: pattern-based detection (no LLM call)."""

    def test_uuid_detected(self) -> None:
        from app.guardrails.output.privacy_filter import _detect_privacy_patterns

        text = "The course ID is a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert _detect_privacy_patterns(text) is True

    def test_postgres_url_detected(self) -> None:
        from app.guardrails.output.privacy_filter import _detect_privacy_patterns

        text = "Connect to postgres://user:pass@localhost:5432/db"
        assert _detect_privacy_patterns(text) is True

    def test_qdrant_url_detected(self) -> None:
        from app.guardrails.output.privacy_filter import _detect_privacy_patterns

        text = "Vector store at http://qdrant:6333"
        assert _detect_privacy_patterns(text) is True

    def test_clean_output_passes(self) -> None:
        from app.guardrails.output.privacy_filter import _detect_privacy_patterns

        text = (
            "I found 3 Python courses for beginners."
            " The top-rated one is ML Specialization with a 4.8 rating."
        )
        assert _detect_privacy_patterns(text) is False

    def test_env_var_detected(self) -> None:
        from app.guardrails.output.privacy_filter import _detect_privacy_patterns

        text = "The OPENAI_API_KEY is set to sk-proj-xxx"
        assert _detect_privacy_patterns(text) is True

    def test_stack_trace_detected(self) -> None:
        from app.guardrails.output.privacy_filter import _detect_privacy_patterns

        text = 'Traceback (most recent call last):\n  File "/app/main.py", line 10'
        assert _detect_privacy_patterns(text) is True


class TestPrivacyGuardrail:
    @pytest.mark.asyncio
    async def test_clean_output_passes(self) -> None:
        from app.guardrails.output.privacy_filter import privacy_guardrail

        llm_response = json.dumps({"privacy_violation": False, "reason": "normal course info"})

        with patch(
            "app.guardrails.output.privacy_filter.Runner.run",
            new_callable=AsyncMock,
            return_value=MagicMock(final_output=llm_response),
        ):
            result = await privacy_guardrail.guardrail_function(
                MagicMock(), MagicMock(), "Here are 3 Python courses for beginners."
            )

        assert result.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_pattern_detected_blocks(self) -> None:
        """Stage 1 pattern detection should block without LLM call."""
        from app.guardrails.output.privacy_filter import privacy_guardrail

        result = await privacy_guardrail.guardrail_function(
            MagicMock(),
            MagicMock(),
            "Course ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        )

        assert result.tripwire_triggered is True
        assert result.output_info["privacy_violation"] is True

    @pytest.mark.asyncio
    async def test_empty_output_passes(self) -> None:
        from app.guardrails.output.privacy_filter import privacy_guardrail

        result = await privacy_guardrail.guardrail_function(MagicMock(), MagicMock(), "")

        assert result.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_llm_detects_violation(self) -> None:
        from app.guardrails.output.privacy_filter import privacy_guardrail

        llm_response = json.dumps(
            {"privacy_violation": True, "reason": "contains internal agent metadata"}
        )

        with patch(
            "app.guardrails.output.privacy_filter.Runner.run",
            new_callable=AsyncMock,
            return_value=MagicMock(final_output=llm_response),
        ):
            result = await privacy_guardrail.guardrail_function(
                MagicMock(),
                MagicMock(),
                "The Triage Agent handed off to Search Agent with context...",
            )

        assert result.tripwire_triggered is True

    @pytest.mark.asyncio
    async def test_runner_error_passes(self) -> None:
        """Fail-open on LLM errors for Stage 2."""
        from app.guardrails.output.privacy_filter import privacy_guardrail

        with patch(
            "app.guardrails.output.privacy_filter.Runner.run",
            new_callable=AsyncMock,
            side_effect=RuntimeError("LLM unavailable"),
        ):
            result = await privacy_guardrail.guardrail_function(
                MagicMock(), MagicMock(), "Some normal output"
            )

        assert result.tripwire_triggered is False


class TestPrivacyPrompt:
    def test_prompt_file_exists(self) -> None:
        prompt_path = (
            Path(__file__).parent.parent.parent.parent
            / "app"
            / "prompts"
            / "guardrails"
            / "privacy.md"
        )
        assert prompt_path.exists()
