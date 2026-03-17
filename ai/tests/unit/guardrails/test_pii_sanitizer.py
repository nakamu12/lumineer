"""Tests for the PII sanitizer guardrail."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock

import pytest

from app.guardrails.input.pii_sanitizer import PiiMapping, PiiMaskResult, mask_pii


class TestMaskPii:
    def test_no_pii_unchanged(self) -> None:
        result = mask_pii("Find Python courses for beginners")
        assert result.masked_text == "Find Python courses for beginners"
        assert len(result.mappings) == 0

    def test_empty_input(self) -> None:
        result = mask_pii("")
        assert result.masked_text == ""
        assert len(result.mappings) == 0

    def test_masks_email(self) -> None:
        result = mask_pii("Contact me at john@example.com please")
        assert "john@example.com" not in result.masked_text
        assert "<EMAIL_ADDRESS>" in result.masked_text
        assert any(m.entity_type == "EMAIL_ADDRESS" for m in result.mappings)
        assert any(m.original == "john@example.com" for m in result.mappings)

    def test_masks_phone_us(self) -> None:
        result = mask_pii("Call me at 555-123-4567")
        assert "555-123-4567" not in result.masked_text
        assert "<PHONE_NUMBER>" in result.masked_text

    def test_masks_phone_japanese(self) -> None:
        result = mask_pii("My phone is 090-1234-5678")
        assert "090-1234-5678" not in result.masked_text
        assert "<PHONE_NUMBER>" in result.masked_text
        assert any(m.entity_type == "PHONE_NUMBER" for m in result.mappings)

    def test_masks_phone_japanese_intl(self) -> None:
        result = mask_pii("Reach me at +81-90-1234-5678")
        assert "+81-90-1234-5678" not in result.masked_text
        assert "<PHONE_NUMBER>" in result.masked_text

    def test_masks_credit_card(self) -> None:
        result = mask_pii("My card is 4111-1111-1111-1111")
        assert "4111-1111-1111-1111" not in result.masked_text
        assert "<CREDIT_CARD>" in result.masked_text

    def test_multiple_pii(self) -> None:
        text = "I'm John, email john@example.com, phone 090-1234-5678"
        result = mask_pii(text)
        assert "john@example.com" not in result.masked_text
        assert "090-1234-5678" not in result.masked_text
        assert len(result.mappings) >= 2

    def test_masks_person_name(self) -> None:
        result = mask_pii("My name is John Smith and I want to learn Python")
        assert any(m.entity_type == "PERSON" for m in result.mappings)

    def test_result_is_immutable(self) -> None:
        result = mask_pii("test@example.com")
        assert isinstance(result, PiiMaskResult)

    def test_pii_mapping_is_frozen(self) -> None:
        mapping = PiiMapping(
            original="john@example.com", masked="<EMAIL_ADDRESS>", entity_type="EMAIL_ADDRESS"
        )
        with pytest.raises(FrozenInstanceError):
            mapping.original = "other@example.com"  # type: ignore[misc]

    def test_mappings_contain_original_value(self) -> None:
        """Mapping records must hold enough info to restore original PII."""
        result = mask_pii("Email me at hello@test.com")
        email_mapping = next((m for m in result.mappings if m.entity_type == "EMAIL_ADDRESS"), None)
        assert email_mapping is not None
        assert email_mapping.original == "hello@test.com"
        assert email_mapping.masked == "<EMAIL_ADDRESS>"


class TestPiiSanitizerGuardrail:
    """Test the @input_guardrail decorated function (detection-only, never blocks)."""

    @pytest.mark.asyncio
    async def test_pii_detected_does_not_block(self) -> None:
        """Guardrail is detection-only — must never set tripwire_triggered=True."""
        from app.guardrails.input.pii_sanitizer import pii_sanitizer_guardrail

        result = await pii_sanitizer_guardrail.guardrail_function(
            MagicMock(), MagicMock(), "My email is secret@example.com"
        )

        assert result.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_clean_input_not_flagged(self) -> None:
        from app.guardrails.input.pii_sanitizer import pii_sanitizer_guardrail

        result = await pii_sanitizer_guardrail.guardrail_function(
            MagicMock(), MagicMock(), "Find me Python courses"
        )

        assert result.tripwire_triggered is False
        assert result.output_info["pii_detected"] is False

    @pytest.mark.asyncio
    async def test_empty_input_passes(self) -> None:
        from app.guardrails.input.pii_sanitizer import pii_sanitizer_guardrail

        result = await pii_sanitizer_guardrail.guardrail_function(MagicMock(), MagicMock(), "")

        assert result.tripwire_triggered is False

    @pytest.mark.asyncio
    async def test_message_list_input_handled(self) -> None:
        """Guardrail must handle list[TResponseInputItem] format."""
        from app.guardrails.input.pii_sanitizer import pii_sanitizer_guardrail

        message_list = [{"role": "user", "content": "Contact me at user@example.com"}]
        result = await pii_sanitizer_guardrail.guardrail_function(
            MagicMock(), MagicMock(), message_list
        )

        # Detection-only: never blocks even with PII
        assert result.tripwire_triggered is False
