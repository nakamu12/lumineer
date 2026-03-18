"""L1 Input Guard: Prompt injection detection.

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

from app.guardrails.input._utils import extract_text

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
    text = extract_text(input_data)
    lower = text.lower()

    is_injection = any(pattern in lower for pattern in _INJECTION_PATTERNS)

    if is_injection:
        run_ctx = ctx.context
        if run_ctx is not None and run_ctx.metrics is not None:
            run_ctx.metrics.record_guardrail_trigger(guardrail_type="injection")

    return GuardrailFunctionOutput(
        output_info={"injection_detected": is_injection, "input_preview": text[:100]},
        tripwire_triggered=is_injection,
    )
