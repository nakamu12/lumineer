"""Path Agent evaluation: Faithfulness + Hallucination via DeepEval.

Runs the Path Agent prompt against pre-defined retrieval contexts from the
Golden Dataset, then evaluates the LLM response quality.

Usage:
    uv run pytest evals/benchmarks/test_path_eval.py -v
    uv run python scripts/run_evals.py --category path
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric, HallucinationMetric
from deepeval.test_case import LLMTestCase
from openai import OpenAI

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PATH_PROMPT_PATH = Path(__file__).parent.parent.parent / "app" / "prompts" / "path.md"

FAITHFULNESS_THRESHOLD = 0.7
HALLUCINATION_THRESHOLD = 0.5  # DeepEval: 0.0 = no hallucination, lower is better


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_path_prompt(query: str, retrieval_context: list[str]) -> str:
    """Build a prompt simulating the Path Agent receiving tool results."""
    system_prompt = PATH_PROMPT_PATH.read_text(encoding="utf-8")
    context_block = "\n".join(retrieval_context)
    return (
        f"{system_prompt}\n\n"
        f"## Learning Path Data (from generate_learning_path tool)\n\n"
        f"{context_block}\n\n"
        f"## User Query\n\n"
        f"{query}"
    )


def _call_llm(prompt: str, model: str = "gpt-4o-mini") -> str:
    """Call OpenAI LLM and return the response text."""
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=2000,
    )
    return response.choices[0].message.content or ""


def _generate_test_cases(
    dataset: list[dict[str, Any]],
) -> list[tuple[str, LLMTestCase]]:
    """Generate DeepEval test cases by calling the LLM for each entry."""
    test_cases: list[tuple[str, LLMTestCase]] = []

    for entry in dataset:
        test_id: str = entry["test_id"]
        query: str = entry["query"]
        retrieval_context: list[str] = entry["retrieval_context"]

        prompt = _build_path_prompt(query, retrieval_context)
        actual_output = _call_llm(prompt)

        test_case = LLMTestCase(
            input=query,
            actual_output=actual_output,
            retrieval_context=retrieval_context,
            context=retrieval_context,
        )
        test_cases.append((test_id, test_case))

    return test_cases


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def path_test_cases(
    path_golden_dataset: list[dict[str, Any]],
) -> list[tuple[str, LLMTestCase]]:
    """Generate all LLM test cases once per module."""
    return _generate_test_cases(path_golden_dataset)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPathFaithfulness:
    """Verify that Path Agent responses are faithful to context."""

    @pytest.fixture(autouse=True)
    def _setup(self, path_test_cases: list[tuple[str, LLMTestCase]]) -> None:
        self._test_cases = path_test_cases

    def test_faithfulness(self) -> None:
        """All test cases should meet the faithfulness threshold."""
        metric = FaithfulnessMetric(
            threshold=FAITHFULNESS_THRESHOLD,
            model="gpt-4o-mini",
        )
        for _test_id, test_case in self._test_cases:
            assert_test(test_case, [metric])


class TestPathHallucination:
    """Verify that Path Agent does not hallucinate."""

    @pytest.fixture(autouse=True)
    def _setup(self, path_test_cases: list[tuple[str, LLMTestCase]]) -> None:
        self._test_cases = path_test_cases

    def test_hallucination(self) -> None:
        """All test cases should meet the hallucination threshold."""
        metric = HallucinationMetric(
            threshold=HALLUCINATION_THRESHOLD,
            model="gpt-4o-mini",
        )
        for _test_id, test_case in self._test_cases:
            assert_test(test_case, [metric])
