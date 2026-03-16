"""OpenAI EmbeddingPort adapter (class-based, for runtime use)."""

import logging

from openai import AsyncOpenAI

from app.domain.ports.embedding import EmbeddingPort

logger = logging.getLogger(__name__)


class OpenAIEmbeddingAdapter(EmbeddingPort):
    """Implements EmbeddingPort using OpenAI text-embedding-3-large."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-large",
        dimensions: int = 3072,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        """Generate a single embedding vector."""
        sanitized = text.strip() or "."
        response = await self._client.embeddings.create(
            input=[sanitized],
            model=self._model,
            dimensions=self._dimensions,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts."""
        sanitized = [t.strip() or "." for t in texts]
        response = await self._client.embeddings.create(
            input=sanitized,
            model=self._model,
            dimensions=self._dimensions,
        )
        return [item.embedding for item in response.data]
