"""Port definition for vector store operations."""

from abc import ABC, abstractmethod
from typing import Any


class VectorStorePort(ABC):
    """Abstract interface for vector store operations."""

    @abstractmethod
    async def hybrid_search(
        self,
        query_vector: list[float],
        query_text: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform hybrid search combining dense and sparse retrieval."""
        ...

    @abstractmethod
    async def upsert(self, points: list[dict[str, Any]]) -> None:
        """Insert or update points in the vector store."""
        ...

    @abstractmethod
    async def get_by_id(self, point_id: str) -> dict[str, Any] | None:
        """Retrieve a single point by its ID."""
        ...
