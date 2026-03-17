"""L4 Output Guard: Privacy filter to prevent internal system info leaks.

Two-stage approach:
  Stage 1: Fast regex pattern matching (UUIDs, connection strings, stack traces).
  Stage 2: LLM classifier for subtler leaks (agent metadata, raw payloads).
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    output_guardrail,
)

from app.config.settings import get_settings

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "guardrails" / "privacy.md"
_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")

# Stage 1 patterns: fast regex checks for obvious leaks
_PRIVACY_PATTERNS: list[re.Pattern[str]] = [
    # UUIDs (e.g. Qdrant point IDs)
    re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        re.IGNORECASE,
    ),
    # PostgreSQL connection strings
    re.compile(r"postgres(?:ql)?://\S+", re.IGNORECASE),
    # Qdrant internal URLs
    re.compile(r"https?://qdrant[:\d/]", re.IGNORECASE),
    # Environment variable keys with sensitive suffixes
    re.compile(r"\b[A-Z_]{2,}_(?:API_KEY|SECRET|PASSWORD|TOKEN)\b"),
    # Python stack traces
    re.compile(r"Traceback \(most recent call last\)"),
    # File path references from stack traces
    re.compile(r'File "/app/.*", line \d+'),
]


def _detect_privacy_patterns(text: str) -> bool:
    """Stage 1: Check text against known privacy-leaking patterns."""
    return any(pattern.search(text) for pattern in _PRIVACY_PATTERNS)


@lru_cache(maxsize=1)
def _create_classifier() -> Agent[None]:
    """Create a cached lightweight LLM classifier for privacy violation detection."""
    settings = get_settings()
    return Agent(
        name="Privacy Classifier",
        instructions=_PROMPT,
        model=settings.LLM_MODEL,
    )


@output_guardrail
async def privacy_guardrail(
    ctx: RunContextWrapper[Any],
    agent: Agent[Any],
    output: str,
) -> GuardrailFunctionOutput:
    """Detect internal system information leaks in agent output."""
    if not output.strip():
        return GuardrailFunctionOutput(
            output_info={"privacy_violation": False},
            tripwire_triggered=False,
        )

    # Stage 1: Fast pattern matching
    if _detect_privacy_patterns(output):
        return GuardrailFunctionOutput(
            output_info={"privacy_violation": True, "reason": "pattern_detected"},
            tripwire_triggered=True,
        )

    # Stage 2: LLM classifier for subtler leaks
    try:
        classifier = _create_classifier()
        result = await Runner.run(classifier, input=output)
        parsed = json.loads(result.final_output)
        is_violation = parsed.get("privacy_violation", False)
        reason = parsed.get("reason", "")
    except (json.JSONDecodeError, KeyError, TypeError):
        # Fail-open on parse errors (defense in depth)
        is_violation = False
        reason = "parse_error"
    except Exception:
        # Fail-open on LLM errors
        is_violation = False
        reason = "classifier_error"

    return GuardrailFunctionOutput(
        output_info={"privacy_violation": is_violation, "reason": reason},
        tripwire_triggered=is_violation,
    )
