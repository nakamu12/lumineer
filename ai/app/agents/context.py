"""Agent run context: observability handles shared across one agent run.

Passed as ``context=`` to ``Runner.run_streamed()`` / ``Runner.run()``.
Guardrails and tools access it through ``ctx.context``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentRunContext:
    """Carries observability handles for one agent invocation.

    All fields are optional — when observability is disabled (e.g. in
    unit tests) pass ``AgentRunContext()`` and each field gracefully
    accepts ``None`` or a no-op object.
    """

    metrics: Any = field(default=None)
    tracer: Any = field(default=None)
    token_tracker: Any = field(default=None)
    # Langfuse trace span for the current request (created by the route handler)
    trace: Any = field(default=None)
