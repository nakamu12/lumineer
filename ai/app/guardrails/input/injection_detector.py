"""L1 Input Guard: Prompt injection detection (skeleton).

Current implementation uses simple keyword matching.
Future: Replace with LLM-based detection using a guardrail agent.
"""

from __future__ import annotations

from typing import Any

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
)

# Patterns that indicate prompt injection attempts
_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "ignore your instructions",
    "disregard previous",
    "disregard your instructions",
    "forget your instructions",
    "override your instructions",
    "you are now",
    "act as if you are",
    "pretend you are",
    "new instructions:",
    "system prompt:",
    "reveal your prompt",
    "show your instructions",
    "output your system",
]


@input_guardrail
async def injection_guardrail(
    ctx: RunContextWrapper[Any],
    agent: Agent[Any],
    input_data: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Detect obvious prompt injection patterns in user input."""
    text = _extract_text(input_data)
    lower = text.lower()

    is_injection = any(pattern in lower for pattern in _INJECTION_PATTERNS)

    return GuardrailFunctionOutput(
        output_info={"injection_detected": is_injection, "input_preview": text[:100]},
        tripwire_triggered=is_injection,
    )


def _extract_text(input_data: str | list[TResponseInputItem]) -> str:
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
