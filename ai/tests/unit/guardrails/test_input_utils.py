"""Tests for shared input guardrail utilities."""

from app.guardrails.input._utils import extract_text


class TestExtractText:
    def test_string_input(self) -> None:
        assert extract_text("hello world") == "hello world"

    def test_message_list_input(self) -> None:
        messages = [
            {"role": "user", "content": "find Python courses"},
        ]
        assert extract_text(messages) == "find Python courses"  # type: ignore[arg-type]

    def test_empty_message_list(self) -> None:
        assert extract_text([]) == ""  # type: ignore[arg-type]

    def test_non_user_messages_ignored(self) -> None:
        messages = [
            {"role": "system", "content": "you are an agent"},
            {"role": "user", "content": "hello"},
        ]
        assert extract_text(messages) == "hello"  # type: ignore[arg-type]

    def test_empty_string(self) -> None:
        assert extract_text("") == ""

    def test_multiple_user_messages(self) -> None:
        messages = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "second"},
        ]
        assert extract_text(messages) == "first second"  # type: ignore[arg-type]
