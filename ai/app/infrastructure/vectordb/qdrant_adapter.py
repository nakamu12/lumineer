"""Qdrant adapter: collection setup and upsert."""

import logging
from typing import Any

from fastembed.sparse import SparseTextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    SparseIndexParams,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

logger = logging.getLogger(__name__)

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"


def create_client(url: str, api_key: str | None = None, timeout: int = 120) -> QdrantClient:
    return QdrantClient(url=url, api_key=api_key, timeout=timeout)


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    dense_size: int = 3072,
    recreate: bool = False,
) -> None:
    """Create collection with dense + sparse vectors if it doesn't exist."""
    exists = client.collection_exists(collection_name)
    if exists and recreate:
        logger.info("Recreating collection '%s'", collection_name)
        client.delete_collection(collection_name)
        exists = False

    if not exists:
        logger.info("Creating collection '%s'", collection_name)
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                DENSE_VECTOR_NAME: VectorParams(
                    size=dense_size,
                    distance=Distance.COSINE,
                )
            },
            sparse_vectors_config={
                SPARSE_VECTOR_NAME: SparseVectorParams(index=SparseIndexParams(on_disk=False))
            },
        )
    else:
        logger.info("Collection '%s' already exists", collection_name)


def build_sparse_vectors(texts: list[str]) -> list[SparseVector]:
    """Generate BM25 sparse vectors for a list of texts using fastembed."""
    model = SparseTextEmbedding(model_name="Qdrant/bm25")
    embeddings = list(model.embed(texts))
    return [
        SparseVector(
            indices=emb.indices.tolist(),
            values=emb.values.tolist(),
        )
        for emb in embeddings
    ]


def build_payload(course: dict[str, Any]) -> dict[str, Any]:
    """Build Qdrant payload from processed course dict."""
    return {
        "title": course["title"],
        "description": course["description"],
        "skills": course["skills"],
        "level": course.get("level"),
        "organization": course["organization"],
        "rating": course["rating"],
        "enrolled": course["enrolled"],
        "num_reviews": course.get("num_reviews"),
        "modules": course.get("modules"),
        "schedule": course.get("schedule"),
        "url": course["url"],
        "instructor": course.get("instructor"),
    }


def upsert_courses(
    client: QdrantClient,
    collection_name: str,
    course_ids: list[str],
    dense_vectors: list[list[float]],
    sparse_vectors: list[SparseVector],
    payloads: list[dict[str, Any]],
    batch_size: int = 200,
    progress_callback: Any = None,
) -> None:
    """Upsert courses into Qdrant in batches."""
    total = len(course_ids)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        points = [
            PointStruct(
                id=course_ids[i],
                vector={
                    DENSE_VECTOR_NAME: dense_vectors[i],
                    SPARSE_VECTOR_NAME: sparse_vectors[i],
                },
                payload=payloads[i],
            )
            for i in range(start, end)
        ]
        client.upsert(collection_name=collection_name, points=points)
        if progress_callback:
            progress_callback(end - start)

    logger.info("Upserted %d courses into '%s'", total, collection_name)
