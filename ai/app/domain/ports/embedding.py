"""Port definition for embedding model operations."""

from abc import ABC, abstractmethod


class EmbeddingPort(ABC):
    """Abstract interface for text embedding operations."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts."""
        ...
