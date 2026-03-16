"""L1 Input Guard: Off-topic detection (skeleton).

Current implementation is a pass-through placeholder.
Future: Replace with LLM-based off-topic detection.

Off-topic boundary:
  - Block: "What's the weather?", "Give me a recipe", etc.
  - Allow: "What career paths need data science?", "Is this certification useful?"
    (grey-zone questions related to learning/education are permitted)
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


@input_guardrail
async def offtopic_guardrail(
    ctx: RunContextWrapper[Any],
    agent: Agent[Any],
    input_data: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Detect off-topic queries (skeleton: always passes)."""
    return GuardrailFunctionOutput(
        output_info={"offtopic_detected": False},
        tripwire_triggered=False,
    )
