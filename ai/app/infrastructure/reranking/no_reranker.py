"""NoReranker: pass-through strategy (baseline)."""

from typing import Any

from app.infrastructure.reranking.base import BaseReranker


class NoReranker(BaseReranker):
    """Returns results as-is (RRF order from Qdrant)."""

    def rerank(
        self,
        query: str,
        results: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        return results[:top_k]
