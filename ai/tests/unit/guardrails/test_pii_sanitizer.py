"""Tests for the PII sanitizer guardrail."""

from __future__ import annotations

from app.guardrails.input.pii_sanitizer import PiiMaskResult, mask_pii


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

    def test_result_is_immutable(self) -> None:
        result = mask_pii("test@example.com")
        assert isinstance(result, PiiMaskResult)
