"""L1 Input Guard: Off-topic detection using LLM-based classification.

Detects queries unrelated to education/courses/learning and blocks them.
Grey-zone questions (career guidance, certification value) are allowed.
Fail-open on errors (defense in depth via other guardrails).
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

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "guardrails" / "offtopic.md"
_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _create_classifier() -> Agent[None]:
    """Create a cached lightweight off-topic classifier agent."""
    settings = get_settings()
    return Agent(
        name="Off-topic Classifier",
        instructions=_PROMPT,
        model=settings.LLM_MODEL,
    )


@input_guardrail
async def offtopic_guardrail(
    ctx: RunContextWrapper[Any],
    agent: Agent[Any],
    input_data: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Detect off-topic queries via LLM classification."""
    text = extract_text(input_data)

    if not text.strip():
        return GuardrailFunctionOutput(
            output_info={"offtopic_detected": False},
            tripwire_triggered=False,
        )

    try:
        classifier = _create_classifier()
        result = await Runner.run(classifier, input=text)
        parsed = json.loads(result.final_output)
        is_offtopic: bool = parsed.get("is_offtopic", False)
        reason: str = parsed.get("reason", "")
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.warning("Off-topic classifier returned unparseable response, failing open")
        is_offtopic = False
        reason = "parse_error"
    except Exception:
        logger.exception("Off-topic classifier error, failing open")
        is_offtopic = False
        reason = "classifier_error"

    return GuardrailFunctionOutput(
        output_info={"offtopic_detected": is_offtopic, "reason": reason},
        tripwire_triggered=is_offtopic,
    )
