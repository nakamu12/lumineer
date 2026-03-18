"""L5 Economic Guard: Token budget tracking and Corrective RAG retry limits.

Tracks per-request token consumption and enforces configurable budgets
to prevent Denial-of-Wallet attacks.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenBudget:
    """Per-request token limits."""

    max_input_tokens: int = 10_000
    max_output_tokens: int = 4_000
    max_total_tokens: int = 14_000
    max_corrective_rag_retries: int = 3


@dataclass
class RequestTokenUsage:
    """Mutable tracker for a single request's token consumption."""

    input_tokens: int = 0
    output_tokens: int = 0
    corrective_rag_retries: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed (input + output)."""
        return self.input_tokens + self.output_tokens

    def record_usage(self, *, input_tokens: int, output_tokens: int) -> None:
        """Accumulate token usage from an LLM call."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def check_budget(self, budget: TokenBudget) -> bool:
        """Return True if usage is within all budget limits."""
        if self.input_tokens > budget.max_input_tokens:
            return False
        if self.output_tokens > budget.max_output_tokens:
            return False
        if self.total_tokens > budget.max_total_tokens:
            return False
        return True

    def can_retry_corrective_rag(self, budget: TokenBudget) -> bool:
        """Return True if Corrective RAG retry is allowed."""
        return self.corrective_rag_retries < budget.max_corrective_rag_retries

    def record_corrective_rag_retry(self) -> None:
        """Increment the Corrective RAG retry counter."""
        self.corrective_rag_retries += 1


class CostTracker:
    """Manages token budgets and usage tracking for requests."""

    def __init__(self, budget: TokenBudget | None = None) -> None:
        self._budget = budget or TokenBudget()

    @property
    def budget(self) -> TokenBudget:
        """Return the configured token budget."""
        return self._budget

    def create_request_usage(self) -> RequestTokenUsage:
        """Create a new usage tracker for a request."""
        return RequestTokenUsage()

    def check_budget(self, usage: RequestTokenUsage) -> bool:
        """Check if usage is within the configured budget."""
        return usage.check_budget(self._budget)
