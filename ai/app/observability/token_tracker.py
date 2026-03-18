"""Token usage tracker — dual-sends to Prometheus and Langfuse."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.observability.langfuse_tracer import LangfuseTracer
from app.observability.metrics import MetricsCollector


@dataclass(frozen=True)
class TokenTracker:
    """Records per-request token consumption in both Prometheus and Langfuse."""

    metrics: MetricsCollector
    tracer: LangfuseTracer

    def track(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        model: str,
        trace: Any = None,
        generation_name: str = "agent-response",
    ) -> None:
        """Record token usage to Prometheus and optionally to Langfuse.

        Args:
            input_tokens: Number of input tokens consumed.
            output_tokens: Number of output tokens consumed.
            model: LLM model identifier (e.g. "gpt-4o-mini").
            trace: An active Langfuse trace object. When provided *and*
                   the tracer is enabled, a generation is logged.
            generation_name: Label for the Langfuse generation entry.
        """
        # Always record to Prometheus
        self.metrics.record_tokens_used(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
        )

        # Conditionally record to Langfuse
        if trace is not None and self.tracer.enabled:
            self.tracer.log_generation(
                trace=trace,
                name=generation_name,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
