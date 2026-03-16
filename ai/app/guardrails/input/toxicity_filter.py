"""L1 Input Guard: Toxicity detection (skeleton).

Current implementation is a pass-through placeholder.
Future: Replace with LLM-based toxicity detection using a guardrail agent.
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
async def toxicity_guardrail(
    ctx: RunContextWrapper[Any],
    agent: Agent[Any],
    input_data: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Detect toxic language in user input (skeleton: always passes)."""
    return GuardrailFunctionOutput(
        output_info={"toxicity_detected": False},
        tripwire_triggered=False,
    )
