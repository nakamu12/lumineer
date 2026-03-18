"""L1 Input Guard: Toxicity detection using LLM-based classification.

Detects toxic language (threats, hate speech, harassment, discrimination)
and blocks the request. Fail-open on errors (defense in depth via other guardrails).
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)

from app.config.settings import get_settings
from app.guardrails.input._utils import extract_text

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "guardrails" / "toxicity.md"
_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _create_classifier() -> Agent[None]:
    """Create a cached lightweight toxicity classifier agent."""
    settings = get_settings()
    return Agent(
        name="Toxicity Classifier",
        instructions=_PROMPT,
        model=settings.LLM_MODEL,
    )


@input_guardrail
async def toxicity_guardrail(
    ctx: RunContextWrapper[Any],
    agent: Agent[Any],
    input_data: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Detect toxic language in user input via LLM classification."""
    text = extract_text(input_data)

    if not text.strip():
        return GuardrailFunctionOutput(
            output_info={"toxicity_detected": False},
            tripwire_triggered=False,
        )

    try:
        classifier = _create_classifier()
        result = await Runner.run(classifier, input=text)
        parsed = json.loads(result.final_output)
        is_toxic: bool = parsed.get("is_toxic", False)
        reason: str = parsed.get("reason", "")
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.warning("Toxicity classifier returned unparseable response, failing open")
        is_toxic = False
        reason = "parse_error"
    except Exception:
        logger.exception("Toxicity classifier error, failing open")
        is_toxic = False
        reason = "classifier_error"

    if is_toxic:
        run_ctx = ctx.context
        if run_ctx is not None and run_ctx.metrics is not None:
            run_ctx.metrics.record_guardrail_trigger(guardrail_type="toxicity")

    return GuardrailFunctionOutput(
        output_info={"toxicity_detected": is_toxic, "reason": reason},
        tripwire_triggered=is_toxic,
    )
