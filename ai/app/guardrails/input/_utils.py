"""Shared utilities for input guardrails."""

from __future__ import annotations

from agents import TResponseInputItem


def extract_text(input_data: str | list[TResponseInputItem]) -> str:
    """Extract plain text from agent input (str or message list)."""
    if isinstance(input_data, str):
        return input_data
    # For message list, extract content from user messages
    parts: list[str] = []
    for item in input_data:
        if isinstance(item, dict) and item.get("role") == "user":
            content = item.get("content", "")
            if isinstance(content, str):
                parts.append(content)
    return " ".join(parts)
