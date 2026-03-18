"""Prometheus metrics definitions for AI Processing service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
    llm_requests: Counter
    llm_latency: Histogram
    llm_cost_usd: Counter
    guardrail_triggers: Counter
    pii_detections: Counter

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

    def record_llm_request(self, *, agent: str, status: str = "success") -> None:
        """Record an LLM request by agent and status."""
        self.llm_requests.labels(agent=agent, status=status).inc()

    def record_llm_latency(self, *, agent: str, duration: float) -> None:
        """Record LLM call latency for an agent."""
        self.llm_latency.labels(agent=agent).observe(duration)

    def record_llm_cost(self, *, model: str, cost_usd: float) -> None:
        """Record estimated LLM API cost in USD."""
        self.llm_cost_usd.labels(model=model).inc(cost_usd)

    def record_guardrail_trigger(self, *, guardrail_type: str) -> None:
        """Record a guardrail trigger event."""
        self.guardrail_triggers.labels(type=guardrail_type).inc()

    def record_pii_detection(self, *, entity_type: str) -> None:
        """Record a PII detection event."""
        self.pii_detections.labels(entity_type=entity_type).inc()


def _get_or_create(metric_cls: type, name: str, description: str, **kwargs: Any) -> Any:
    """Return existing metric if already registered, else create new one.

    On hot-reload the default registry already contains the metric.
    We unregister it first to allow clean re-creation.
    """
    reg = kwargs.get("registry", DEFAULT_REGISTRY)
    # Check all name variants (Counter adds _total, _created suffixes)
    existing = reg._names_to_collectors.get(name) or reg._names_to_collectors.get(f"{name}_total")
    if existing is not None:
        try:
            reg.unregister(existing)
        except Exception:
            pass
    return metric_cls(name, description, **kwargs)


def create_metrics_collector(*, registry: CollectorRegistry | None = None) -> MetricsCollector:
    """Create a MetricsCollector with the given (or default) registry."""
    reg = registry or REGISTRY

    request_duration = _get_or_create(
        Histogram,
        "ai_request_duration_seconds",
        "AI service HTTP request duration in seconds",
        labelnames=["endpoint", "method"],
        registry=reg,
    )

    request_errors = _get_or_create(
        Counter,
        "ai_request_errors_total",
        "Total AI service HTTP request errors",
        labelnames=["endpoint", "method"],
        registry=reg,
    )

    tokens_used = _get_or_create(
        Counter,
        "ai_tokens_used_total",
        "Total tokens consumed by AI service",
        labelnames=["type", "model"],
        registry=reg,
    )

    agent_handoffs = _get_or_create(
        Counter,
        "ai_agent_handoffs_total",
        "Total agent handoffs",
        labelnames=["from_agent", "to_agent"],
        registry=reg,
    )

    llm_requests = _get_or_create(
        Counter,
        "ai_llm_requests_total",
        "Total LLM requests by agent and status",
        labelnames=["agent", "status"],
        registry=reg,
    )

    llm_latency = _get_or_create(
        Histogram,
        "ai_llm_latency_seconds",
        "LLM call latency in seconds",
        labelnames=["agent"],
        registry=reg,
    )

    llm_cost_usd = _get_or_create(
        Counter,
        "ai_llm_cost_usd_total",
        "Estimated LLM API cost in USD",
        labelnames=["model"],
        registry=reg,
    )

    guardrail_triggers = _get_or_create(
        Counter,
        "ai_guardrail_triggers_total",
        "Total guardrail trigger events",
        labelnames=["type"],
        registry=reg,
    )

    pii_detections = _get_or_create(
        Counter,
        "ai_pii_detections_total",
        "Total PII detection events",
        labelnames=["entity_type"],
        registry=reg,
    )

    return MetricsCollector(
        request_duration=request_duration,
        request_errors=request_errors,
        tokens_used=tokens_used,
        agent_handoffs=agent_handoffs,
        llm_requests=llm_requests,
        llm_latency=llm_latency,
        llm_cost_usd=llm_cost_usd,
        guardrail_triggers=guardrail_triggers,
        pii_detections=pii_detections,
    )
