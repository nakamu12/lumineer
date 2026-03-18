"""Langfuse tracing integration for LLM observability."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from langfuse import Langfuse

logger = logging.getLogger(__name__)


class _NoopSpan:
    """Sentinel span returned when Langfuse is disabled."""

    def end(self) -> None:  # noqa: PLR6301
        pass


_NOOP_SPAN = _NoopSpan()


@dataclass
class LangfuseTracer:
    """Wrapper around the Langfuse client for LLM tracing.

    When ``enabled`` is False every method is a no-op so callers
    never need to check the flag themselves.
    """

    enabled: bool = False
    _client: Langfuse | None = field(default=None, repr=False)

    # -- public API -----------------------------------------------------------

    def create_trace(
        self,
        *,
        name: str,
    ) -> Any:
        """Start a new Langfuse trace span (or return a no-op sentinel).

        Uses the Langfuse SDK v3 ``start_span()`` API which is based on
        OpenTelemetry internally.
        """
        if not self.enabled or self._client is None:
            return _NOOP_SPAN

        return self._client.start_span(name=name)

    def log_generation(
        self,
        *,
        trace: Any,
        name: str,
        model: str,
        input_data: Any = None,
        output_data: Any = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Log an LLM generation on an existing trace span.

        IMPORTANT: ``input_data`` and ``output_data`` are forwarded to
        Langfuse as-is.  Callers MUST pass pre-masked text (e.g. via
        Presidio) to avoid storing PII in the Langfuse backend.
        """
        if not self.enabled or isinstance(trace, _NoopSpan):
            return

        gen = self._client.start_generation(  # type: ignore[union-attr]
            name=name,
            model=model,
            input=input_data,
            output=output_data,
            usage_details={"input": input_tokens, "output": output_tokens},
        )
        gen.end()

    def flush(self) -> None:
        """Flush any pending events to Langfuse."""
        if self._client is not None:
            self._client.flush()


def create_langfuse_tracer(
    *,
    public_key: str | None,
    secret_key: str | None,
    host: str | None,
) -> LangfuseTracer:
    """Factory: create a LangfuseTracer.

    Returns a disabled (no-op) tracer when either key is missing.
    """
    if not public_key or not secret_key:
        logger.info("Langfuse keys not configured — tracing disabled")
        return LangfuseTracer(enabled=False)

    client = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host or "http://localhost:3003",
    )
    logger.info("Langfuse tracing enabled (host=%s)", host)
    return LangfuseTracer(enabled=True, _client=client)
