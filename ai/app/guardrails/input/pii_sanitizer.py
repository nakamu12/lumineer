"""L1 Input Guard: PII masking using Microsoft Presidio.

Masks personally identifiable information before sending to LLM.
Detected entities: PERSON, EMAIL_ADDRESS, PHONE_NUMBER, CREDIT_CARD.
Includes custom recognizer for Japanese phone number patterns.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Any

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
)
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from app.guardrails.input._utils import extract_text

logger = logging.getLogger(__name__)

# Entities to detect
_ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD"]


@dataclass(frozen=True)
class PiiMapping:
    """Immutable record of a single PII replacement."""

    original: str
    masked: str
    entity_type: str


@dataclass(frozen=True)
class PiiMaskResult:
    """Result of PII masking operation."""

    masked_text: str
    mappings: tuple[PiiMapping, ...]


def _build_japanese_phone_recognizer() -> PatternRecognizer:
    """Create a custom recognizer for Japanese phone number patterns."""
    jp_patterns = [
        Pattern(
            name="jp_mobile",
            regex=r"0[789]0-?\d{4}-?\d{4}",
            score=0.85,
        ),
        Pattern(
            name="jp_landline",
            regex=r"0\d{1,4}-?\d{1,4}-?\d{4}",
            score=0.7,
        ),
        Pattern(
            name="jp_intl",
            regex=r"\+81-?\d{1,2}-?\d{4}-?\d{4}",
            score=0.9,
        ),
    ]
    return PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        patterns=jp_patterns,
        name="JapanesePhoneRecognizer",
        supported_language="en",
    )


def _create_analyzer() -> AnalyzerEngine:
    """Create a Presidio analyzer with custom Japanese phone recognizer."""
    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
    )
    nlp_engine = provider.create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
    analyzer.registry.add_recognizer(_build_japanese_phone_recognizer())
    return analyzer


def _create_anonymizer() -> AnonymizerEngine:
    """Create a Presidio anonymizer engine."""
    return AnonymizerEngine()  # type: ignore[no-untyped-call]


# Lazy-initialized singletons (avoid import-time spaCy model loading).
# Thread lock prevents double-initialization under concurrent requests.
_init_lock = threading.Lock()
_analyzer: AnalyzerEngine | None = None
_anonymizer: AnonymizerEngine | None = None


def _get_analyzer() -> AnalyzerEngine:
    """Return cached Presidio analyzer (thread-safe lazy initialization)."""
    global _analyzer  # noqa: PLW0603
    if _analyzer is None:
        with _init_lock:
            if _analyzer is None:
                _analyzer = _create_analyzer()
    return _analyzer


def _get_anonymizer() -> AnonymizerEngine:
    """Return cached Presidio anonymizer (thread-safe lazy initialization)."""
    global _anonymizer  # noqa: PLW0603
    if _anonymizer is None:
        with _init_lock:
            if _anonymizer is None:
                _anonymizer = _create_anonymizer()
    return _anonymizer


def mask_pii(text: str) -> PiiMaskResult:
    """Mask PII in text and return masked text with mapping for restoration.

    Args:
        text: Input text potentially containing PII.

    Returns:
        PiiMaskResult with masked text and tuple of PiiMapping records.
    """
    if not text:
        return PiiMaskResult(masked_text="", mappings=())

    # Analyze text for PII entities
    analyzer = _get_analyzer()
    results = analyzer.analyze(text=text, entities=_ENTITIES, language="en")

    if not results:
        return PiiMaskResult(masked_text=text, mappings=())

    # Build operator config for consistent placeholder format
    operators = {
        entity: OperatorConfig("replace", {"new_value": f"<{entity}>"}) for entity in _ENTITIES
    }

    anonymizer = _get_anonymizer()
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,  # type: ignore[arg-type]
        operators=operators,
    )

    # Build mappings from analysis results
    mappings: list[PiiMapping] = []
    for result_item in results:
        original_value = text[result_item.start : result_item.end]
        mappings.append(
            PiiMapping(
                original=original_value,
                masked=f"<{result_item.entity_type}>",
                entity_type=result_item.entity_type,
            )
        )

    return PiiMaskResult(
        masked_text=anonymized.text,
        mappings=tuple(mappings),
    )


@input_guardrail
async def pii_sanitizer_guardrail(
    ctx: RunContextWrapper[Any],
    agent: Agent[Any],
    input_data: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Safety-net guardrail: detect unmasked PII in input (log only, never blocks).

    This is a detection-only guardrail. The actual masking is done by mask_pii()
    as a preprocessing step in the route handler before Runner.run().
    """
    text = extract_text(input_data)
    if not text.strip():
        return GuardrailFunctionOutput(
            output_info={"pii_detected": False},
            tripwire_triggered=False,
        )

    try:
        analyzer = _get_analyzer()
        results = analyzer.analyze(text=text, entities=_ENTITIES, language="en")
        pii_found = len(results) > 0
        if pii_found:
            entity_types = list({r.entity_type for r in results})
            logger.warning("Unmasked PII detected in input: %s", entity_types)
            # Record each unique PII entity type in Prometheus
            run_ctx = ctx.context
            if run_ctx is not None and run_ctx.metrics is not None:
                for entity_type in entity_types:
                    run_ctx.metrics.record_pii_detection(entity_type=entity_type)
    except Exception:
        logger.exception("PII detection error in safety-net guardrail")
        pii_found = False

    return GuardrailFunctionOutput(
        output_info={"pii_detected": pii_found},
        tripwire_triggered=False,  # Never blocks — detection only
    )
