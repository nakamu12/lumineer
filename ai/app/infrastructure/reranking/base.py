"""Base interface for all reranker strategies."""

from abc import ABC, abstractmethod
from typing import Any


class BaseReranker(ABC):
    """Strategy interface for result reranking."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        results: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Rerank search results and return the top_k entries."""
        ...
