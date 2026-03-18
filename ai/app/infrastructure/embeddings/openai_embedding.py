"""OpenAI text-embedding-3-large adapter."""

import logging
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def embed_batch(
    client: OpenAI,
    texts: list[str],
    model: str = "text-embedding-3-large",
    dimensions: int = 3072,
) -> list[list[float]]:
    """Generate dense embeddings for a batch of texts."""
    # Replace empty strings to avoid API errors
    sanitized = [t if t.strip() else "." for t in texts]
    response = client.embeddings.create(
        input=sanitized,
        model=model,
        dimensions=dimensions,
    )
    return [item.embedding for item in response.data]


def embed_all(
    client: OpenAI,
    texts: list[str],
    model: str = "text-embedding-3-large",
    dimensions: int = 3072,
    batch_size: int = 100,
    progress_callback: Any = None,
) -> list[list[float]]:
    """Generate embeddings for all texts in batches."""
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        embeddings = embed_batch(client, batch, model=model, dimensions=dimensions)
        all_embeddings.extend(embeddings)
        if progress_callback:
            progress_callback(len(batch))
    return all_embeddings
