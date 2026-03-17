"""Run LLM evaluations and check Tier 1 thresholds.

Usage:
    uv run python scripts/run_evals.py                      # Run all evals
    uv run python scripts/run_evals.py --category search     # Search only
    uv run python scripts/run_evals.py --category skill_gap  # Skill Gap only
    uv run python scripts/run_evals.py --category path       # Path only
    uv run python scripts/run_evals.py --verbose             # Detailed output

Exit codes:
    0 — All Tier 1 thresholds passed
    1 — One or more thresholds failed
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tier 1 thresholds (ADR-012-7)
# ---------------------------------------------------------------------------

THRESHOLDS: dict[str, dict[str, float]] = {
    "faithfulness": {"min": 0.7},  # higher is better (1.0 = perfectly faithful)
    "hallucination": {"max": 0.5},  # lower is better (0.0 = no hallucination)
}

DATASETS_DIR = Path(__file__).parent.parent / "evals" / "datasets"
PROMPTS_DIR = Path(__file__).parent.parent / "app" / "prompts"

CATEGORIES = ("search", "skill_gap", "path")


# ---------------------------------------------------------------------------
# Langfuse eval logger (optional — gracefully disabled when keys are absent)
# ---------------------------------------------------------------------------


class _LangfuseEvalLogger:
    """Thin wrapper around Langfuse SDK for eval result logging.

    Creates one Langfuse trace per eval run (category + run_id) and logs
    individual test-case scores as child spans + Langfuse score events.
    Disabled automatically when LANGFUSE_PUBLIC_KEY is absent.
    """

    def __init__(self) -> None:
        from app.config.settings import get_settings

        settings = get_settings()
        if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
            logger.info("Langfuse keys absent — eval results will NOT be sent to Langfuse")
            self._client = None
            return
        try:
            from langfuse import Langfuse  # type: ignore[import-not-found]

            self._client = Langfuse(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST,
            )
            logger.info("Langfuse eval logger initialised (host=%s)", settings.LANGFUSE_HOST)
        except Exception:
            logger.exception("Failed to initialise Langfuse client — continuing without it")
            self._client = None

    @property
    def enabled(self) -> bool:
        """Return True if Langfuse is available."""
        return self._client is not None

    def log_test_case(
        self,
        *,
        category: str,
        test_id: str,
        query: str,
        faithfulness: float,
        hallucination: float,
        passed: bool,
    ) -> None:
        """Log a single eval test-case result as a Langfuse trace + scores."""
        if self._client is None:
            return
        try:
            trace = self._client.trace(
                name="eval-test-case",
                metadata={
                    "category": category,
                    "test_id": test_id,
                    "query": query[:200],
                    "passed": passed,
                },
                tags=["eval", category],
            )
            self._client.score(
                trace_id=trace.id,
                name="faithfulness",
                value=faithfulness,
                comment=f"Tier 1 threshold >= {THRESHOLDS['faithfulness']['min']:.2f}",
            )
            self._client.score(
                trace_id=trace.id,
                name="hallucination",
                value=hallucination,
                comment=f"Tier 1 threshold <= {THRESHOLDS['hallucination']['max']:.2f}",
            )
        except Exception:
            logger.exception("Langfuse score logging failed for %s/%s", category, test_id)

    def log_category_summary(
        self,
        *,
        category: str,
        avg_faithfulness: float,
        avg_hallucination: float,
        passed: bool,
    ) -> None:
        """Log an aggregated category summary trace to Langfuse."""
        if self._client is None:
            return
        try:
            trace = self._client.trace(
                name="eval-category-summary",
                metadata={
                    "category": category,
                    "avg_faithfulness": avg_faithfulness,
                    "avg_hallucination": avg_hallucination,
                    "passed": passed,
                },
                tags=["eval", "summary", category],
            )
            self._client.score(
                trace_id=trace.id,
                name="avg_faithfulness",
                value=avg_faithfulness,
            )
            self._client.score(
                trace_id=trace.id,
                name="avg_hallucination",
                value=avg_hallucination,
            )
        except Exception:
            logger.exception("Langfuse summary logging failed for %s", category)

    def flush(self) -> None:
        """Flush all pending Langfuse events."""
        if self._client is not None:
            try:
                self._client.flush()
            except Exception:
                logger.exception("Langfuse flush failed")


# Map category -> (prompt file, tool context header)
CATEGORY_CONFIG: dict[str, tuple[str, str]] = {
    "search": ("search.md", "Search Results (from search_courses tool)"),
    "skill_gap": (
        "skill_gap.md",
        "Skill Gap Analysis Results (from analyze_skill_gap tool)",
    ),
    "path": (
        "path.md",
        "Learning Path Data (from generate_learning_path tool)",
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_dataset(name: str) -> list[dict[str, Any]]:
    """Load a Golden Dataset."""
    if name not in CATEGORIES:
        raise ValueError(f"Unknown dataset name: {name!r}")
    path = DATASETS_DIR / f"{name}_golden.json"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    with open(path, encoding="utf-8") as f:
        data: list[dict[str, Any]] = json.load(f)
    return data


def build_prompt(category: str, query: str, retrieval_context: list[str]) -> str:
    """Build a prompt for any agent category."""
    prompt_file, header = CATEGORY_CONFIG[category]
    system_prompt = (PROMPTS_DIR / prompt_file).read_text(encoding="utf-8")
    context_block = "\n".join(retrieval_context)
    return f"{system_prompt}\n\n## {header}\n\n{context_block}\n\n## User Query\n\n{query}"


def call_llm(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 1500) -> str:
    """Call OpenAI LLM and return the response text."""
    from openai import OpenAI

    client = OpenAI(timeout=60.0)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def run_category_evals(
    category: str,
    dataset: list[dict[str, Any]],
    verbose: bool = False,
    langfuse_logger: _LangfuseEvalLogger | None = None,
) -> dict[str, float]:
    """Run eval for a category and return average scores."""
    from deepeval.metrics import FaithfulnessMetric, HallucinationMetric
    from deepeval.test_case import LLMTestCase

    faithfulness_metric = FaithfulnessMetric(threshold=0.7, model="gpt-4o-mini")
    hallucination_metric = HallucinationMetric(threshold=0.5, model="gpt-4o-mini")

    faithfulness_scores: list[float] = []
    hallucination_scores: list[float] = []

    # Path agent produces longer output
    max_tokens = 2000 if category == "path" else 1500

    total = len(dataset)
    for i, entry in enumerate(dataset, 1):
        test_id: str = entry["test_id"]
        query: str = entry["query"]
        retrieval_context: list[str] = entry["retrieval_context"]

        print(f"  [{i}/{total}] {test_id}: {query[:50]}...", flush=True)

        prompt = build_prompt(category, query, retrieval_context)
        actual_output = call_llm(prompt, max_tokens=max_tokens)

        test_case = LLMTestCase(
            input=query,
            actual_output=actual_output,
            retrieval_context=retrieval_context,
            context=retrieval_context,
        )

        faithfulness_metric.measure(test_case)
        hallucination_metric.measure(test_case)

        f_score = faithfulness_metric.score or 0.0
        h_score = hallucination_metric.score or 0.0

        faithfulness_scores.append(f_score)
        hallucination_scores.append(h_score)

        case_passed = (
            f_score >= THRESHOLDS["faithfulness"]["min"]
            and h_score <= THRESHOLDS["hallucination"]["max"]
        )

        if verbose:
            print(f"         Faithfulness: {f_score:.2f}  Hallucination: {h_score:.2f}")
            if f_score < THRESHOLDS["faithfulness"]["min"]:
                print("         [WARN] Faithfulness below threshold")
            if h_score > THRESHOLDS["hallucination"]["max"]:
                print("         [WARN] Hallucination above threshold")

        # Log individual test-case result to Langfuse
        if langfuse_logger is not None:
            langfuse_logger.log_test_case(
                category=category,
                test_id=test_id,
                query=query,
                faithfulness=f_score,
                hallucination=h_score,
                passed=case_passed,
            )

    avg_faithfulness = (
        sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0
    )
    avg_hallucination = (
        sum(hallucination_scores) / len(hallucination_scores) if hallucination_scores else 0
    )

    # Log category summary to Langfuse
    if langfuse_logger is not None:
        summary_passed = (
            avg_faithfulness >= THRESHOLDS["faithfulness"]["min"]
            and avg_hallucination <= THRESHOLDS["hallucination"]["max"]
        )
        langfuse_logger.log_category_summary(
            category=category,
            avg_faithfulness=avg_faithfulness,
            avg_hallucination=avg_hallucination,
            passed=summary_passed,
        )

    return {
        "faithfulness": avg_faithfulness,
        "hallucination": avg_hallucination,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM evaluations")
    parser.add_argument(
        "--category",
        choices=[*CATEGORIES, "all"],
        default="all",
        help="Eval category to run (default: all)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    print("=" * 60)
    print("Lumineer LLM Evaluation")
    print("=" * 60)

    # Initialise Langfuse logger (no-op when keys are absent)
    langfuse_logger = _LangfuseEvalLogger()
    if langfuse_logger.enabled:
        print("Langfuse: results will be logged")
    else:
        print("Langfuse: disabled (set LANGFUSE_PUBLIC_KEY to enable)")

    all_passed = True
    results: dict[str, dict[str, float]] = {}

    categories_to_run = CATEGORIES if args.category == "all" else (args.category,)

    for category in categories_to_run:
        label = category.replace("_", " ").title()
        print(f"\n--- {label} Agent Eval ---")
        dataset = load_dataset(category)
        print(f"Loaded {len(dataset)} test cases")
        scores = run_category_evals(
            category, dataset, verbose=args.verbose, langfuse_logger=langfuse_logger
        )
        results[category] = scores

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    for category, scores in results.items():
        label = category.replace("_", " ").upper()
        print(f"\n  {label}:")
        for metric_name, score in scores.items():
            metric_thresholds = THRESHOLDS.get(metric_name, {})
            if "min" in metric_thresholds:
                threshold = metric_thresholds["min"]
                passed = score >= threshold
                direction = ">="
            elif "max" in metric_thresholds:
                threshold = metric_thresholds["max"]
                passed = score <= threshold
                direction = "<="
            else:
                threshold = 0.0
                passed = True
                direction = "n/a"
            status = "PASS" if passed else "FAIL"
            print(f"    {metric_name:20s}: {score:.3f} ({direction} {threshold:.2f}) [{status}]")
            if not passed:
                all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TIER 1 THRESHOLDS PASSED")
    else:
        print("TIER 1 THRESHOLD FAILURE - Review results above")
    print("=" * 60)

    # Flush any buffered Langfuse events before exit
    langfuse_logger.flush()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
