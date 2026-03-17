"""Tests for the PII restorer output utility."""

from __future__ import annotations

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
        mapping = PiiMapping(original="test", masked="<PERSON>", entity_type="PERSON")
        assert hasattr(mapping, "__dataclass_fields__")
