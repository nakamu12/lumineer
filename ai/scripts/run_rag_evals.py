"""Run RAG pipeline evaluations (requires Qdrant).

Evaluates the full search pipeline: Embed -> Qdrant Hybrid Search -> Rerank -> Results.
Measures retrieval quality using Hit Rate, MRR, and NDCG@k against Golden Datasets.

Usage:
    uv run python scripts/run_rag_evals.py                      # All categories
    uv run python scripts/run_rag_evals.py --category search     # Search only
    uv run python scripts/run_rag_evals.py --reranker heuristic  # Test specific reranker
    uv run python scripts/run_rag_evals.py --verbose             # Detailed output

Prerequisites:
    - Qdrant running locally (docker compose up -d)
    - Data seeded (uv run python scripts/seed_data.py)
    - .env.local with OPENAI_API_KEY and QDRANT_URL

Exit codes:
    0 — All thresholds passed
    1 — One or more thresholds failed
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Thresholds (ADR-012-7)
# ---------------------------------------------------------------------------

THRESHOLDS: dict[str, dict[str, float]] = {
    "hit_rate@10": {"min": 0.6},  # higher is better (1.0 = all queries hit)
    "mrr": {"min": 0.4},  # higher is better (1.0 = always rank 1)
}

DATASETS_DIR = Path(__file__).parent.parent / "evals" / "datasets"
CATEGORIES = ("search", "skill_gap", "path")


# ---------------------------------------------------------------------------
# Retrieval metrics
# ---------------------------------------------------------------------------


def hit_rate_at_k(
    retrieved_titles: list[str],
    expected_titles: list[str],
    k: int = 10,
) -> float:
    """Return 1.0 if any expected title appears in top-k retrieved, else 0.0."""
    top_k = [t.lower().strip() for t in retrieved_titles[:k]]
    for expected in expected_titles:
        if expected.lower().strip() in top_k:
            return 1.0
    return 0.0


def reciprocal_rank(
    retrieved_titles: list[str],
    expected_titles: list[str],
) -> float:
    """Return 1/rank of the first expected title found, or 0.0."""
    retrieved_lower = [t.lower().strip() for t in retrieved_titles]
    expected_lower = {t.lower().strip() for t in expected_titles}
    for i, title in enumerate(retrieved_lower):
        if title in expected_lower:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(
    retrieved_titles: list[str],
    expected_titles: list[str],
    k: int = 10,
) -> float:
    """Compute NDCG@k with binary relevance."""
    retrieved_lower = [t.lower().strip() for t in retrieved_titles[:k]]
    expected_lower = {t.lower().strip() for t in expected_titles}

    # DCG: sum of 1/log2(rank+1) for relevant items
    dcg = 0.0
    for i, title in enumerate(retrieved_lower):
        if title in expected_lower:
            dcg += 1.0 / math.log2(i + 2)  # i+2 because rank starts at 1

    # Ideal DCG: all expected items at top positions
    num_relevant = min(len(expected_titles), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(num_relevant))

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


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


async def run_category_rag_evals(
    category: str,
    dataset: list[dict[str, Any]],
    reranker_strategy: str,
    formatter: str,
    verbose: bool = False,
) -> dict[str, float]:
    """Run RAG retrieval evaluation for a category.

    Imports are deferred to avoid requiring Qdrant/OpenAI at module load time,
    since this script is only run manually (not imported by the app).
    """
    from app.config.container import build_container
    from app.config.settings import get_settings
    from app.domain.usecases.search_courses import SearchCoursesUseCase, SearchQuery
    from app.infrastructure.formatters import create_formatter
    from app.infrastructure.reranking import create_reranker

    settings = get_settings()
    container = build_container()

    reranker = create_reranker(reranker_strategy)
    fmt = create_formatter(formatter)

    usecase = SearchCoursesUseCase(
        vector_store=container.vector_store,
        embedding=container.embedding,
        reranker=reranker,
        formatter=fmt,
    )

    hit_rates: list[float] = []
    mrrs: list[float] = []
    ndcgs: list[float] = []

    total = len(dataset)
    for i, entry in enumerate(dataset, 1):
        test_id: str = entry["test_id"]
        query_text: str = entry["query"]
        expected_courses: list[str] = entry.get("expected_courses", [])

        if not expected_courses:
            if verbose:
                print(f"  [{i}/{total}] {test_id}: skipped (no expected_courses)")
            continue

        print(f"  [{i}/{total}] {test_id}: {query_text[:50]}...", flush=True)

        try:
            search_query = SearchQuery(
                query=query_text,
                limit=10,
                threshold=settings.SIMILARITY_THRESHOLD,
            )

            result = await usecase.execute(search_query)
            retrieved_titles = [c.title for c in result.courses]
        except Exception as e:
            print(f"         [ERROR] {type(e).__name__}: {e}", file=sys.stderr)
            hit_rates.append(0.0)
            mrrs.append(0.0)
            ndcgs.append(0.0)
            continue

        hr = hit_rate_at_k(retrieved_titles, expected_courses, k=10)
        rr = reciprocal_rank(retrieved_titles, expected_courses)
        ndcg = ndcg_at_k(retrieved_titles, expected_courses, k=10)

        hit_rates.append(hr)
        mrrs.append(rr)
        ndcgs.append(ndcg)

        if verbose:
            status = "HIT" if hr > 0 else "MISS"
            print(f"         [{status}] MRR: {rr:.2f}  NDCG@10: {ndcg:.2f}")
            if hr == 0:
                print(f"         Expected: {expected_courses}")
                print(f"         Got: {retrieved_titles[:5]}")

    if not hit_rates:
        print(f"  WARNING: No evaluable test cases for {category}")
        return {"hit_rate@10": 0.0, "mrr": 0.0, "ndcg@10": 0.0}

    n = len(hit_rates)
    return {
        "hit_rate@10": sum(hit_rates) / n,
        "mrr": sum(mrrs) / n,
        "ndcg@10": sum(ndcgs) / n,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG pipeline evaluations")
    parser.add_argument(
        "--category",
        choices=[*CATEGORIES, "all"],
        default="all",
        help="Eval category to run (default: all)",
    )
    parser.add_argument(
        "--reranker",
        choices=["none", "heuristic", "cross-encoder"],
        default="none",
        help="Reranker strategy to evaluate (default: none)",
    )
    parser.add_argument(
        "--formatter",
        choices=["json", "toon"],
        default="json",
        help="Context formatter to use (default: json)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    print("=" * 60)
    print("Lumineer RAG Evaluation")
    print(f"  Reranker: {args.reranker}  |  Formatter: {args.formatter}")
    print("=" * 60)

    all_passed = True
    results: dict[str, dict[str, float]] = {}

    categories_to_run = CATEGORIES if args.category == "all" else (args.category,)

    for category in categories_to_run:
        label = category.replace("_", " ").title()
        print(f"\n--- {label} RAG Eval ---")
        dataset = load_dataset(category)
        # Filter entries that have expected_courses
        with_expected = [e for e in dataset if e.get("expected_courses")]
        print(f"Loaded {len(with_expected)} test cases with expected_courses")

        if not with_expected:
            print("  No expected_courses — skipping")
            continue

        scores = asyncio.run(
            run_category_rag_evals(
                category,
                with_expected,
                reranker_strategy=args.reranker,
                formatter=args.formatter,
                verbose=args.verbose,
            )
        )
        results[category] = scores

    # Print summary
    print("\n" + "=" * 60)
    print("RAG RESULTS SUMMARY")
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
        print("ALL RAG THRESHOLDS PASSED")
    else:
        print("RAG THRESHOLD FAILURE - Review results above")
    print("=" * 60)

    # Strategy comparison hint
    if args.reranker == "none":
        print("\nTip: Compare strategies with:")
        print("  uv run python scripts/run_rag_evals.py --reranker heuristic -v")
        print("  uv run python scripts/run_rag_evals.py --reranker cross-encoder -v")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
