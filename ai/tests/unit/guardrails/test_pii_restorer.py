"""Tests for the PII restorer output utility."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.guardrails.output.pii_restorer import PiiMapping, restore_pii


class TestRestorePii:
    def test_no_mappings(self) -> None:
        text = "Here are 3 Python courses for beginners."
        result = restore_pii(text, ())
        assert result == text

    def test_empty_text(self) -> None:
        assert restore_pii("", ()) == ""

    def test_single_mapping(self) -> None:
        mappings = (
            PiiMapping(
                original="taro@example.com",
                masked="<EMAIL_ADDRESS>",
                entity_type="EMAIL_ADDRESS",
            ),
        )
        text = "We sent a confirmation to <EMAIL_ADDRESS>."
        result = restore_pii(text, mappings)
        assert result == "We sent a confirmation to taro@example.com."

    def test_multiple_mappings(self) -> None:
        mappings = (
            PiiMapping(
                original="Taro Yamada",
                masked="<PERSON>",
                entity_type="PERSON",
            ),
            PiiMapping(
                original="taro@example.com",
                masked="<EMAIL_ADDRESS>",
                entity_type="EMAIL_ADDRESS",
            ),
        )
        text = "Hello <PERSON>, your email is <EMAIL_ADDRESS>."
        result = restore_pii(text, mappings)
        assert result == "Hello Taro Yamada, your email is taro@example.com."

    def test_repeated_placeholder(self) -> None:
        mappings = (PiiMapping(original="Taro", masked="<PERSON>", entity_type="PERSON"),)
        text = "<PERSON> said hello. Then <PERSON> left."
        result = restore_pii(text, mappings)
        assert result == "Taro said hello. Then Taro left."

    def test_mapping_not_in_text(self) -> None:
        mappings = (
            PiiMapping(
                original="secret@mail.com",
                masked="<EMAIL_ADDRESS>",
                entity_type="EMAIL_ADDRESS",
            ),
        )
        text = "No placeholders here."
        result = restore_pii(text, mappings)
        assert result == "No placeholders here."

    def test_immutability(self) -> None:
        """PiiMapping must be a frozen dataclass."""
        mapping = PiiMapping(original="test", masked="<PERSON>", entity_type="PERSON")
        with pytest.raises(FrozenInstanceError):
            mapping.original = "other"  # type: ignore[misc]


class TestPiiRoundTrip:
    """Round-trip tests: simulate the L1 mask → LLM → L4 restore flow."""

    def test_email_round_trip(self) -> None:
        """Masked email placeholder is correctly restored after LLM processing."""
        original_text = "Please contact me at user@example.com for the course info."

        # Simulate what L1 pii_sanitizer produces
        mappings = (
            PiiMapping(
                original="user@example.com",
                masked="<EMAIL_ADDRESS>",
                entity_type="EMAIL_ADDRESS",
            ),
        )
        masked_text = original_text.replace("user@example.com", "<EMAIL_ADDRESS>")

        # Simulate LLM response using the masked text
        llm_response = f"I will send the info to {masked_text.split('at ')[1].split(' for')[0]}."

        # L4 restorer restores PII
        restored = restore_pii(llm_response, mappings)

        assert "user@example.com" in restored
        assert "<EMAIL_ADDRESS>" not in restored

    def test_phone_round_trip(self) -> None:
        """Phone number placeholder is correctly restored."""
        mappings = (
            PiiMapping(
                original="090-1234-5678",
                masked="<PHONE_NUMBER>",
                entity_type="PHONE_NUMBER",
            ),
        )
        llm_output = "I can reach you at <PHONE_NUMBER> if needed."
        restored = restore_pii(llm_output, mappings)

        assert "090-1234-5678" in restored
        assert "<PHONE_NUMBER>" not in restored

    def test_multiple_entity_types_round_trip(self) -> None:
        """Multiple PII types are all restored correctly."""
        mappings = (
            PiiMapping(original="Hanako Tanaka", masked="<PERSON>", entity_type="PERSON"),
            PiiMapping(original="hanako@mail.com", masked="<EMAIL_ADDRESS>", entity_type="EMAIL_ADDRESS"),
        )
        llm_output = "Hello <PERSON>, I sent the confirmation to <EMAIL_ADDRESS>."
        restored = restore_pii(llm_output, mappings)

        assert "Hanako Tanaka" in restored
        assert "hanako@mail.com" in restored
        assert "<PERSON>" not in restored
        assert "<EMAIL_ADDRESS>" not in restored

    def test_no_pii_in_input_passes_through(self) -> None:
        """When no PII was masked, restore_pii returns the text unchanged."""
        text = "Here are the top Python courses from Coursera."
        restored = restore_pii(text, ())
        assert restored == text
