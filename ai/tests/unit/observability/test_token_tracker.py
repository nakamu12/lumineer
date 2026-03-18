"""Unit tests for token tracker module."""

from unittest.mock import MagicMock

from app.observability.token_tracker import TokenTracker


class TestTokenTracker:
    """Tests for TokenTracker dual-send to Prometheus + Langfuse."""

    def test_track_sends_to_metrics(self):
        """Token usage is recorded in Prometheus metrics."""
        mock_metrics = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.enabled = False

        tracker = TokenTracker(metrics=mock_metrics, tracer=mock_tracer)
        tracker.track(
            input_tokens=100,
            output_tokens=50,
            model="gpt-4o-mini",
        )

        mock_metrics.record_tokens_used.assert_called_once_with(
            input_tokens=100,
            output_tokens=50,
            model="gpt-4o-mini",
        )

    def test_track_sends_to_langfuse_when_trace_provided(self):
        """Token usage is logged to Langfuse when trace is provided."""
        mock_metrics = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.enabled = True
        mock_trace = MagicMock()

        tracker = TokenTracker(metrics=mock_metrics, tracer=mock_tracer)
        tracker.track(
            input_tokens=100,
            output_tokens=50,
            model="gpt-4o-mini",
            trace=mock_trace,
            generation_name="agent-chat",
        )

        mock_metrics.record_tokens_used.assert_called_once()
        mock_tracer.log_generation.assert_called_once()
        call_kwargs = mock_tracer.log_generation.call_args[1]
        assert call_kwargs["input_tokens"] == 100
        assert call_kwargs["output_tokens"] == 50
        assert call_kwargs["model"] == "gpt-4o-mini"

    def test_track_skips_langfuse_when_no_trace(self):
        """Langfuse logging is skipped when no trace is provided."""
        mock_metrics = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.enabled = True

        tracker = TokenTracker(metrics=mock_metrics, tracer=mock_tracer)
        tracker.track(input_tokens=10, output_tokens=5, model="gpt-4o-mini")

        mock_metrics.record_tokens_used.assert_called_once()
        mock_tracer.log_generation.assert_not_called()

    def test_track_skips_langfuse_when_tracer_disabled(self):
        """Langfuse logging is skipped when tracer is disabled."""
        mock_metrics = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.enabled = False
        mock_trace = MagicMock()

        tracker = TokenTracker(metrics=mock_metrics, tracer=mock_tracer)
        tracker.track(
            input_tokens=10,
            output_tokens=5,
            model="gpt-4o-mini",
            trace=mock_trace,
        )

        mock_metrics.record_tokens_used.assert_called_once()
        mock_tracer.log_generation.assert_not_called()

    def test_track_with_zero_tokens(self):
        """Zero tokens are still recorded (valid case for cached responses)."""
        mock_metrics = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.enabled = False

        tracker = TokenTracker(metrics=mock_metrics, tracer=mock_tracer)
        tracker.track(input_tokens=0, output_tokens=0, model="gpt-4o-mini")

        mock_metrics.record_tokens_used.assert_called_once_with(
            input_tokens=0, output_tokens=0, model="gpt-4o-mini"
        )
