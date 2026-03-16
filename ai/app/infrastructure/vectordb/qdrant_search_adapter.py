"""Qdrant VectorStorePort adapter: Hybrid Search with RRF."""

from __future__ import annotations

import logging
from typing import Any

from fastembed.sparse import SparseTextEmbedding
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchAny,
    MatchValue,
    Prefetch,
    Range,
    SparseVector,
)

from app.domain.ports.vector_store import VectorStorePort

logger = logging.getLogger(__name__)

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"


class QdrantSearchAdapter(VectorStorePort):
    """Implements VectorStorePort using Qdrant hybrid search with RRF fusion."""

    def __init__(
        self,
        url: str,
        collection_name: str,
        api_key: str | None = None,
        prefetch_limit: int = 20,
    ) -> None:
        self._client = AsyncQdrantClient(url=url, api_key=api_key)
        self._collection = collection_name
        self._prefetch_limit = prefetch_limit
        self._sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    def _build_sparse_vector(self, text: str) -> SparseVector:
        embeddings = list(self._sparse_model.embed([text]))
        emb = embeddings[0]
        return SparseVector(
            indices=emb.indices.tolist(),
            values=emb.values.tolist(),
        )

    def _build_filter(self, filters: dict[str, Any] | None) -> Filter | None:
        if not filters:
            return None

        conditions: list[Any] = []

        if level := filters.get("level"):
            # include courses with null level too (missing data is OK)
            conditions.append(
                Filter(
                    should=[
                        FieldCondition(key="level", match=MatchValue(value=str(level))),
                        FieldCondition(key="level", is_null=True),
                    ]
                )
            )

        if organization := filters.get("organization"):
            conditions.append(
                FieldCondition(key="organization", match=MatchValue(value=str(organization)))
            )

        if min_rating := filters.get("min_rating"):
            conditions.append(FieldCondition(key="rating", range=Range(gte=float(min_rating))))

        if skills := filters.get("skills"):
            conditions.append(FieldCondition(key="skills", match=MatchAny(any=list(skills))))

        if not conditions:
            return None

        return Filter(must=conditions)

    async def hybrid_search(
        self,
        query_vector: list[float],
        query_text: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Hybrid search: Dense + Sparse with RRF fusion."""
        sparse_vector = self._build_sparse_vector(query_text)
        qdrant_filter = self._build_filter(filters)

        results = await self._client.query_points(
            collection_name=self._collection,
            prefetch=[
                Prefetch(
                    query=query_vector,
                    using=DENSE_VECTOR_NAME,
                    limit=self._prefetch_limit,
                    filter=qdrant_filter,
                ),
                Prefetch(
                    query=sparse_vector,
                    using=SPARSE_VECTOR_NAME,
                    limit=self._prefetch_limit,
                    filter=qdrant_filter,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=limit,
            with_payload=True,
        )

        hits = []
        for point in results.points:
            payload = dict(point.payload or {})
            payload["_id"] = str(point.id)
            payload["_score"] = point.score
            hits.append(payload)

        logger.debug("hybrid_search returned %d hits for query=%r", len(hits), query_text)
        return hits

    async def upsert(self, points: list[dict[str, Any]]) -> None:
        """Not implemented for search adapter (use ingestion scripts)."""
        raise NotImplementedError("Use seed_data.py for ingestion")

    async def get_by_id(self, point_id: str) -> dict[str, Any] | None:
        """Retrieve a single point by ID."""
        results = await self._client.retrieve(
            collection_name=self._collection,
            ids=[point_id],
            with_payload=True,
        )
        if not results:
            return None
        payload = dict(results[0].payload or {})
        payload["_id"] = str(results[0].id)
        return payload
