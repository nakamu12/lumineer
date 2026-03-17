"""Tests for the cost tracker."""

from __future__ import annotations

from app.guardrails.system.cost_tracker import CostTracker, RequestTokenUsage, TokenBudget


class TestTokenBudget:
    def test_default_values(self) -> None:
        budget = TokenBudget()
        assert budget.max_input_tokens == 10_000
        assert budget.max_output_tokens == 4_000
        assert budget.max_total_tokens == 14_000
        assert budget.max_corrective_rag_retries == 3

    def test_custom_values(self) -> None:
        budget = TokenBudget(max_input_tokens=5000, max_corrective_rag_retries=1)
        assert budget.max_input_tokens == 5000
        assert budget.max_corrective_rag_retries == 1


class TestRequestTokenUsage:
    def test_initial_state(self) -> None:
        usage = RequestTokenUsage()
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0
        assert usage.corrective_rag_retries == 0

    def test_record_usage(self) -> None:
        usage = RequestTokenUsage()
        usage.record_usage(input_tokens=100, output_tokens=50)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150

    def test_record_usage_accumulates(self) -> None:
        usage = RequestTokenUsage()
        usage.record_usage(input_tokens=100, output_tokens=50)
        usage.record_usage(input_tokens=200, output_tokens=100)
        assert usage.input_tokens == 300
        assert usage.output_tokens == 150
        assert usage.total_tokens == 450

    def test_within_budget(self) -> None:
        budget = TokenBudget(max_input_tokens=1000, max_output_tokens=500, max_total_tokens=1500)
        usage = RequestTokenUsage()
        usage.record_usage(input_tokens=500, output_tokens=200)
        assert usage.check_budget(budget) is True

    def test_exceeds_input_budget(self) -> None:
        budget = TokenBudget(max_input_tokens=100, max_output_tokens=500, max_total_tokens=1500)
        usage = RequestTokenUsage()
        usage.record_usage(input_tokens=200, output_tokens=0)
        assert usage.check_budget(budget) is False

    def test_exceeds_output_budget(self) -> None:
        budget = TokenBudget(max_input_tokens=1000, max_output_tokens=100, max_total_tokens=1500)
        usage = RequestTokenUsage()
        usage.record_usage(input_tokens=0, output_tokens=200)
        assert usage.check_budget(budget) is False

    def test_exceeds_total_budget(self) -> None:
        budget = TokenBudget(max_input_tokens=10000, max_output_tokens=10000, max_total_tokens=100)
        usage = RequestTokenUsage()
        usage.record_usage(input_tokens=60, output_tokens=50)
        assert usage.check_budget(budget) is False

    def test_corrective_rag_retry_allowed(self) -> None:
        budget = TokenBudget(max_corrective_rag_retries=3)
        usage = RequestTokenUsage()
        assert usage.can_retry_corrective_rag(budget) is True

    def test_corrective_rag_retry_blocked(self) -> None:
        budget = TokenBudget(max_corrective_rag_retries=2)
        usage = RequestTokenUsage()
        usage.record_corrective_rag_retry()
        usage.record_corrective_rag_retry()
        assert usage.can_retry_corrective_rag(budget) is False

    def test_record_corrective_rag_retry(self) -> None:
        usage = RequestTokenUsage()
        usage.record_corrective_rag_retry()
        assert usage.corrective_rag_retries == 1
        usage.record_corrective_rag_retry()
        assert usage.corrective_rag_retries == 2


class TestCostTracker:
    def test_create_request_usage(self) -> None:
        tracker = CostTracker()
        usage = tracker.create_request_usage()
        assert isinstance(usage, RequestTokenUsage)
        assert usage.total_tokens == 0

    def test_check_budget_within(self) -> None:
        tracker = CostTracker()
        usage = tracker.create_request_usage()
        usage.record_usage(input_tokens=100, output_tokens=50)
        assert tracker.check_budget(usage) is True

    def test_check_budget_exceeded(self) -> None:
        tracker = CostTracker(TokenBudget(max_total_tokens=100))
        usage = tracker.create_request_usage()
        usage.record_usage(input_tokens=60, output_tokens=50)
        assert tracker.check_budget(usage) is False

    def test_default_budget(self) -> None:
        tracker = CostTracker()
        assert tracker.budget.max_total_tokens == 14_000
