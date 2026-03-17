"""Tests for the hallucination checker guardrail.

Current implementation is a skeleton (always passes).
Tests verify the expected interface contract so that when the
2-stage implementation (DB lookup + LLM Verifier) is added,
the existing test suite catches regressions.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestHallucinationGuardrail:
    """Test the @output_guardrail decorated function."""

    @pytest.mark.asyncio
    async def test_clean_output_passes(self) -> None:
        """Output that contains only retrieved courses should not be blocked."""
        from app.guardrails.output.hallucination_checker import hallucination_guardrail

        output = (
            "I found 3 great Python courses for beginners. "
            "The top pick is 'Python for Everybody' from the University of Michigan."
        )
        result = await hallucination_guardrail.guardrail_function(MagicMock(), MagicMock(), output)

        assert result.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_empty_output_passes(self) -> None:
        from app.guardrails.output.hallucination_checker import hallucination_guardrail

        result = await hallucination_guardrail.guardrail_function(MagicMock(), MagicMock(), "")

        assert result.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_output_info_contains_hallucination_detected_key(self) -> None:
        """Result must expose 'hallucination_detected' in output_info."""
        from app.guardrails.output.hallucination_checker import hallucination_guardrail

        result = await hallucination_guardrail.guardrail_function(
            MagicMock(), MagicMock(), "Here are some courses."
        )

        assert "hallucination_detected" in result.output_info

    @pytest.mark.asyncio
    async def test_returns_guardrail_function_output_type(self) -> None:
        from agents import GuardrailFunctionOutput

        from app.guardrails.output.hallucination_checker import hallucination_guardrail

        result = await hallucination_guardrail.guardrail_function(
            MagicMock(), MagicMock(), "Some output text"
        )

        assert isinstance(result, GuardrailFunctionOutput)


class TestHallucinationCheckerContract:
    """Verify the 2-stage detection contract for future implementation.

    These tests define the EXPECTED behaviour of the real implementation.
    They currently pass because the skeleton always returns False.
    Once Stage 1 and Stage 2 are implemented, add specific hallucination
    scenarios here that MUST be blocked.
    """

    @pytest.mark.asyncio
    async def test_fabricated_course_scenario(self) -> None:
        """Placeholder: output mentioning a course not in retrieved set.

        With the skeleton implementation this passes (fail-open).
        Once Stage 1 DB-lookup is implemented, this test should be
        updated to assert tripwire_triggered=True.
        """
        from app.guardrails.output.hallucination_checker import hallucination_guardrail

        # Course name that was NOT in the retrieval results
        output = "I recommend 'Advanced Quantum Computing with PyTorch' from MIT."
        result = await hallucination_guardrail.guardrail_function(MagicMock(), MagicMock(), output)

        # Current skeleton: passes (False). Future: should be True.
        assert result.tripwire_triggered is False  # noqa: S101 — intentional skeleton check

    @pytest.mark.asyncio
    async def test_real_course_scenario(self) -> None:
        """Output mentioning a real Coursera course should not be blocked."""
        from app.guardrails.output.hallucination_checker import hallucination_guardrail

        output = (
            "Based on your interest in machine learning, I recommend "
            "'Machine Learning Specialization' by Andrew Ng on Coursera. "
            "It has a 4.9 rating and is suitable for beginners."
        )
        result = await hallucination_guardrail.guardrail_function(MagicMock(), MagicMock(), output)

        assert result.tripwire_triggered is False
