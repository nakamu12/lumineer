"""Prometheus metrics definitions for AI Processing service."""

from __future__ import annotations

from dataclasses import dataclass

from prometheus_client import REGISTRY as DEFAULT_REGISTRY
from prometheus_client import CollectorRegistry, Counter, Histogram

# Module-level reference so tests can patch it
REGISTRY = DEFAULT_REGISTRY


@dataclass(frozen=True)
class MetricsCollector:
    """Collects and exposes Prometheus metrics for the AI service."""

    request_duration: Histogram
    request_errors: Counter
    tokens_used: Counter
    agent_handoffs: Counter

    def record_request_duration(self, *, endpoint: str, method: str, duration: float) -> None:
        """Record HTTP request duration in seconds."""
        self.request_duration.labels(endpoint=endpoint, method=method).observe(duration)

    def record_request_error(self, *, endpoint: str, method: str) -> None:
        """Increment error counter for an endpoint."""
        self.request_errors.labels(endpoint=endpoint, method=method).inc()

    def record_tokens_used(self, *, input_tokens: int, output_tokens: int, model: str) -> None:
        """Record token consumption by type."""
        self.tokens_used.labels(type="input", model=model).inc(input_tokens)
        self.tokens_used.labels(type="output", model=model).inc(output_tokens)

    def record_agent_handoff(self, *, from_agent: str, to_agent: str) -> None:
        """Record an agent-to-agent handoff."""
        self.agent_handoffs.labels(from_agent=from_agent, to_agent=to_agent).inc()


def create_metrics_collector(*, registry: CollectorRegistry | None = None) -> MetricsCollector:
    """Create a MetricsCollector with the given (or default) registry."""
    reg = registry or REGISTRY

    request_duration = Histogram(
        "ai_request_duration_seconds",
        "AI service HTTP request duration in seconds",
        labelnames=["endpoint", "method"],
        registry=reg,
    )

    request_errors = Counter(
        "ai_request_errors_total",
        "Total AI service HTTP request errors",
        labelnames=["endpoint", "method"],
        registry=reg,
    )

    tokens_used = Counter(
        "ai_tokens_used_total",
        "Total tokens consumed by AI service",
        labelnames=["type", "model"],
        registry=reg,
    )

    agent_handoffs = Counter(
        "ai_agent_handoffs_total",
        "Total agent handoffs",
        labelnames=["from_agent", "to_agent"],
        registry=reg,
    )

    return MetricsCollector(
        request_duration=request_duration,
        request_errors=request_errors,
        tokens_used=tokens_used,
        agent_handoffs=agent_handoffs,
    )
