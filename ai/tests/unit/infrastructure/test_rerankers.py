"""Unit tests for Reranker strategies."""

import pytest

from app.infrastructure.reranking import (
    HeuristicReranker,
    NoReranker,
    create_reranker,
)
from app.infrastructure.reranking.base import BaseReranker


def _make_results(n: int = 5) -> list[dict]:  # type: ignore[type-arg]
    return [
        {
            "_id": str(i),
            "_score": 1.0 - i * 0.1,
            "title": f"Course {i}",
            "description": f"Description {i}",
            "rating": 5.0 - i * 0.3,
            "enrolled": (5 - i) * 10_000,
        }
        for i in range(n)
    ]


class TestNoReranker:
    def test_returns_top_k(self) -> None:
        results = _make_results(5)
        reranked = NoReranker().rerank("query", results, top_k=3)
        assert len(reranked) == 3

    def test_preserves_order(self) -> None:
        results = _make_results(5)
        reranked = NoReranker().rerank("query", results, top_k=5)
        assert [r["_id"] for r in reranked] == [str(i) for i in range(5)]

    def test_empty_input(self) -> None:
        assert NoReranker().rerank("query", [], top_k=10) == []

    def test_top_k_larger_than_results(self) -> None:
        results = _make_results(3)
        reranked = NoReranker().rerank("query", results, top_k=10)
        assert len(reranked) == 3


class TestHeuristicReranker:
    def test_returns_top_k(self) -> None:
        results = _make_results(5)
        reranked = HeuristicReranker().rerank("query", results, top_k=3)
        assert len(reranked) == 3

    def test_higher_rating_promoted_when_relevance_equal(self) -> None:
        # Both items have identical relevance; rating and enrolled decide the winner
        results = [
            {"_id": "low", "_score": 0.8, "title": "Low", "rating": 1.0, "enrolled": 100},
            {"_id": "high", "_score": 0.8, "title": "High", "rating": 5.0, "enrolled": 1_000_000},
        ]
        reranked = HeuristicReranker().rerank("query", results, top_k=2)
        assert reranked[0]["_id"] == "high"

    def test_empty_input(self) -> None:
        assert HeuristicReranker().rerank("query", [], top_k=10) == []

    def test_single_result(self) -> None:
        results = _make_results(1)
        reranked = HeuristicReranker().rerank("query", results, top_k=1)
        assert len(reranked) == 1


class TestCreateReranker:
    def test_none(self) -> None:
        assert isinstance(create_reranker("none"), NoReranker)

    def test_heuristic(self) -> None:
        assert isinstance(create_reranker("heuristic"), HeuristicReranker)

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown reranker"):
            create_reranker("unknown-strategy")

    def test_all_are_base_reranker(self) -> None:
        for strategy in ("none", "heuristic"):
            assert isinstance(create_reranker(strategy), BaseReranker)
