"""Unit tests for Langfuse tracer module."""

from unittest.mock import MagicMock, patch

from app.observability.langfuse_tracer import _NoopSpan, create_langfuse_tracer


class TestLangfuseTracerDisabled:
    """Tests for LangfuseTracer when Langfuse is not configured."""

    def test_disabled_when_no_keys(self):
        """Tracer is disabled (no-op) when keys are not provided."""
        tracer = create_langfuse_tracer(public_key=None, secret_key=None, host=None)
        assert tracer.enabled is False

    def test_disabled_when_partial_keys(self):
        """Tracer is disabled when only some keys are provided."""
        tracer = create_langfuse_tracer(public_key="pk-123", secret_key=None, host=None)
        assert tracer.enabled is False

    def test_trace_is_noop_when_disabled(self):
        """Creating a trace returns a no-op span when disabled."""
        tracer = create_langfuse_tracer(public_key=None, secret_key=None, host=None)
        trace = tracer.create_trace(name="test-trace")
        assert isinstance(trace, _NoopSpan)

    def test_generation_is_noop_when_disabled(self):
        """Logging a generation is a no-op when disabled."""
        tracer = create_langfuse_tracer(public_key=None, secret_key=None, host=None)
        trace = tracer.create_trace(name="test-trace")
        # Should not raise
        tracer.log_generation(
            trace=trace,
            name="test-gen",
            model="gpt-4o-mini",
            input_data="hello",
            output_data="world",
            input_tokens=10,
            output_tokens=5,
        )

    def test_flush_is_noop_when_disabled(self):
        """Flush does nothing when disabled."""
        tracer = create_langfuse_tracer(public_key=None, secret_key=None, host=None)
        tracer.flush()  # Should not raise


class TestLangfuseTracerEnabled:
    """Tests for LangfuseTracer when Langfuse is configured."""

    @patch("app.observability.langfuse_tracer.Langfuse")
    def test_enabled_when_keys_provided(self, mock_langfuse_cls: MagicMock):
        """Tracer is enabled when all keys are provided."""
        tracer = create_langfuse_tracer(
            public_key="pk-123",
            secret_key="sk-456",
            host="http://localhost:3003",
        )
        assert tracer.enabled is True
        mock_langfuse_cls.assert_called_once()

    @patch("app.observability.langfuse_tracer.Langfuse")
    def test_create_trace_delegates_to_client(self, mock_langfuse_cls: MagicMock):
        """Creating a trace calls the Langfuse client."""
        mock_client = MagicMock()
        mock_langfuse_cls.return_value = mock_client

        tracer = create_langfuse_tracer(
            public_key="pk-123",
            secret_key="sk-456",
            host="http://localhost:3003",
        )
        tracer.create_trace(name="test-trace")

        mock_client.start_span.assert_called_once_with(name="test-trace")

    @patch("app.observability.langfuse_tracer.Langfuse")
    def test_log_generation_delegates_to_client(self, mock_langfuse_cls: MagicMock):
        """Logging a generation calls client.start_generation()."""
        mock_client = MagicMock()
        mock_gen = MagicMock()
        mock_langfuse_cls.return_value = mock_client
        mock_client.start_generation.return_value = mock_gen

        tracer = create_langfuse_tracer(
            public_key="pk-123",
            secret_key="sk-456",
            host="http://localhost:3003",
        )
        trace = MagicMock()  # Non-noop trace
        tracer.log_generation(
            trace=trace,
            name="agent-response",
            model="gpt-4o-mini",
            input_data="What is Python?",
            output_data="Python is a programming language.",
            input_tokens=10,
            output_tokens=20,
        )

        mock_client.start_generation.assert_called_once()
        call_kwargs = mock_client.start_generation.call_args[1]
        assert call_kwargs["name"] == "agent-response"
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["usage_details"]["input"] == 10
        assert call_kwargs["usage_details"]["output"] == 20
        mock_gen.end.assert_called_once()

    @patch("app.observability.langfuse_tracer.Langfuse")
    def test_flush_delegates_to_client(self, mock_langfuse_cls: MagicMock):
        """Flush calls the Langfuse client flush."""
        mock_client = MagicMock()
        mock_langfuse_cls.return_value = mock_client

        tracer = create_langfuse_tracer(
            public_key="pk-123",
            secret_key="sk-456",
            host="http://localhost:3003",
        )
        tracer.flush()
        mock_client.flush.assert_called_once()
