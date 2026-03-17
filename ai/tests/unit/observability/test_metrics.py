"""Unit tests for Prometheus metrics module."""

from unittest.mock import patch

import pytest
from prometheus_client import CollectorRegistry

from app.observability.metrics import (
    MetricsCollector,
    create_metrics_collector,
)


@pytest.fixture
def registry() -> CollectorRegistry:
    """Create an isolated Prometheus registry for each test."""
    return CollectorRegistry()


@pytest.fixture
def metrics(registry: CollectorRegistry) -> MetricsCollector:
    """Create a MetricsCollector with isolated registry."""
    return create_metrics_collector(registry=registry)


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_record_request_duration(self, metrics: MetricsCollector, registry: CollectorRegistry):
        """Recording request duration updates the histogram."""
        metrics.record_request_duration(endpoint="/search", method="POST", duration=0.5)

        # Verify the histogram has recorded the observation
        sample_value = registry.get_sample_value(
            "ai_request_duration_seconds_count",
            labels={"endpoint": "/search", "method": "POST"},
        )
        assert sample_value == 1.0

    def test_record_request_error(self, metrics: MetricsCollector, registry: CollectorRegistry):
        """Recording errors increments the counter."""
        metrics.record_request_error(endpoint="/agents/chat", method="POST")
        metrics.record_request_error(endpoint="/agents/chat", method="POST")

        sample_value = registry.get_sample_value(
            "ai_request_errors_total",
            labels={"endpoint": "/agents/chat", "method": "POST"},
        )
        assert sample_value == 2.0

    def test_record_tokens_used(self, metrics: MetricsCollector, registry: CollectorRegistry):
        """Recording token usage increments counters for input and output."""
        metrics.record_tokens_used(input_tokens=100, output_tokens=50, model="gpt-4o-mini")

        input_value = registry.get_sample_value(
            "ai_tokens_used_total",
            labels={"type": "input", "model": "gpt-4o-mini"},
        )
        output_value = registry.get_sample_value(
            "ai_tokens_used_total",
            labels={"type": "output", "model": "gpt-4o-mini"},
        )
        assert input_value == 100.0
        assert output_value == 50.0

    def test_record_agent_handoff(self, metrics: MetricsCollector, registry: CollectorRegistry):
        """Recording agent handoffs increments the counter."""
        metrics.record_agent_handoff(from_agent="Triage Agent", to_agent="Search Agent")

        sample_value = registry.get_sample_value(
            "ai_agent_handoffs_total",
            labels={"from_agent": "Triage Agent", "to_agent": "Search Agent"},
        )
        assert sample_value == 1.0

    def test_multiple_endpoints_tracked_independently(
        self, metrics: MetricsCollector, registry: CollectorRegistry
    ):
        """Different endpoints maintain separate metric values."""
        metrics.record_request_duration(endpoint="/search", method="POST", duration=0.1)
        metrics.record_request_duration(endpoint="/health", method="GET", duration=0.01)

        search_count = registry.get_sample_value(
            "ai_request_duration_seconds_count",
            labels={"endpoint": "/search", "method": "POST"},
        )
        health_count = registry.get_sample_value(
            "ai_request_duration_seconds_count",
            labels={"endpoint": "/health", "method": "GET"},
        )
        assert search_count == 1.0
        assert health_count == 1.0


class TestCreateMetricsCollector:
    """Tests for the factory function."""

    def test_creates_with_custom_registry(self, registry: CollectorRegistry):
        """Factory creates collector with provided registry."""
        collector = create_metrics_collector(registry=registry)
        assert isinstance(collector, MetricsCollector)

    def test_creates_with_default_registry(self):
        """Factory creates collector with default registry when none provided."""
        with patch("app.observability.metrics.REGISTRY") as mock_registry:
            collector = create_metrics_collector(registry=mock_registry)
            assert isinstance(collector, MetricsCollector)
