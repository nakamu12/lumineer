"""Reranking strategy implementations."""

from app.infrastructure.reranking.base import BaseReranker
from app.infrastructure.reranking.cross_encoder_reranker import CrossEncoderReranker
from app.infrastructure.reranking.heuristic_reranker import HeuristicReranker
from app.infrastructure.reranking.no_reranker import NoReranker

__all__ = ["BaseReranker", "NoReranker", "HeuristicReranker", "CrossEncoderReranker"]


def create_reranker(strategy: str) -> BaseReranker:
    """Factory: create reranker from strategy name."""
    match strategy:
        case "none":
            return NoReranker()
        case "heuristic":
            return HeuristicReranker()
        case "cross-encoder":
            return CrossEncoderReranker()
        case _:
            raise ValueError(f"Unknown reranker strategy: {strategy!r}")
