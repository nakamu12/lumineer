"""L4 Output Guard: Hallucination detection (skeleton).

Current implementation is a pass-through placeholder.

Future 2-stage approach:
  Stage 1: DB lookup (cost $0) — check if course names in the output
           exist in the retrieved_courses set.
  Stage 2: LLM Verifier (parallel) — verify context faithfulness
           using @output_guardrail with a dedicated guardrail agent.
"""

from __future__ import annotations

from typing import Any

from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, output_guardrail


@output_guardrail
async def hallucination_guardrail(
    ctx: RunContextWrapper[Any],
    agent: Agent[Any],
    output: Any,
) -> GuardrailFunctionOutput:
    """Detect hallucinated course information (skeleton: always passes)."""
    return GuardrailFunctionOutput(
        output_info={"hallucination_detected": False},
        tripwire_triggered=False,
    )
