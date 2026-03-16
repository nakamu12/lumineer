"""SearchCoursesUseCase: orchestrates the RAG search pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.domain.entities.course import CourseEntity, CourseFactory
from app.domain.ports.embedding import EmbeddingPort
from app.domain.ports.vector_store import VectorStorePort
from app.infrastructure.formatters.base import BaseFormatter
from app.infrastructure.reranking.base import BaseReranker

logger = logging.getLogger(__name__)

# Denial-of-Wallet protection: max corrective-RAG retries
MAX_CORRECTIVE_RETRIES = 2


@dataclass
class SearchQuery:
    """Input parameters for a course search request."""

    query: str
    level: str | None = None
    organization: str | None = None
    min_rating: float | None = None
    skills: list[str] | None = None
    limit: int = 10
    threshold: float = 0.7
    prefetch_limit: int = 20


@dataclass
class SearchResult:
    """Output of a successful search."""

    courses: list[CourseEntity]
    formatted_context: str
    total_hits: int
    reranker_applied: str
    formatter_applied: str


def _payload_to_entity(payload: dict[str, Any]) -> CourseEntity:
    """Convert a Qdrant payload dict to a CourseEntity."""
    return CourseFactory.create(
        id=payload.get("_id"),
        title=payload.get("title", ""),
        description=payload.get("description", ""),
        skills=payload.get("skills") or [],
        level=payload.get("level"),
        organization=payload.get("organization", ""),
        rating=float(payload.get("rating", 0.0)),
        enrolled=int(payload.get("enrolled", 0)),
        num_reviews=payload.get("num_reviews"),
        modules=payload.get("modules"),
        schedule=payload.get("schedule"),
        url=payload.get("url", ""),
        instructor=payload.get("instructor"),
        search_text="",
    )


class SearchCoursesUseCase:
    """
    RAG search pipeline:
      Embed → Hybrid Search → Threshold filter → Rerank → Format

    Corrective RAG: if results fall below threshold, broaden the query
    by stripping metadata filters and retrying (up to MAX_CORRECTIVE_RETRIES).
    """

    def __init__(
        self,
        vector_store: VectorStorePort,
        embedding: EmbeddingPort,
        reranker: BaseReranker,
        formatter: BaseFormatter,
    ) -> None:
        self._vector_store = vector_store
        self._embedding = embedding
        self._reranker = reranker
        self._formatter = formatter

    async def execute(self, query: SearchQuery) -> SearchResult:
        filters: dict[str, Any] = {}
        if query.level:
            filters["level"] = query.level
        if query.organization:
            filters["organization"] = query.organization
        if query.min_rating is not None:
            filters["min_rating"] = query.min_rating
        if query.skills:
            filters["skills"] = query.skills

        courses = await self._search_with_corrective_rag(query, filters)
        formatted = self._formatter.format(courses)

        return SearchResult(
            courses=courses,
            formatted_context=formatted,
            total_hits=len(courses),
            reranker_applied=type(self._reranker).__name__,
            formatter_applied=type(self._formatter).__name__,
        )

    async def _search_with_corrective_rag(
        self,
        query: SearchQuery,
        filters: dict[str, Any],
    ) -> list[CourseEntity]:
        """Search with optional corrective RAG when results are too few."""
        query_vector = await self._embedding.embed(query.query)
        hits: list[dict[str, Any]] = []

        for attempt in range(MAX_CORRECTIVE_RETRIES + 1):
            raw = await self._vector_store.hybrid_search(
                query_vector=query_vector,
                query_text=query.query,
                limit=query.prefetch_limit,
                filters=filters if filters else None,
            )

            above_threshold = [r for r in raw if float(r.get("_score", 0.0)) >= query.threshold]

            if above_threshold or attempt == MAX_CORRECTIVE_RETRIES:
                hits = above_threshold or raw  # fallback: use all if nothing passes threshold
                break

            logger.info(
                "Corrective RAG attempt %d: 0 results above threshold %.2f, relaxing filters",
                attempt + 1,
                query.threshold,
            )
            filters = {}  # broaden: drop all metadata filters

        # Build entity list preserving Qdrant order
        entities = [_payload_to_entity(h) for h in hits]

        # Rerank using raw dicts so rerankers can access _score / rating / enrolled
        reranked_raw = self._reranker.rerank(
            query=query.query,
            results=hits,
            top_k=query.limit,
        )

        # Map reranked raw dicts back to entities by _id
        id_to_entity = {e.id: e for e in entities}
        reranked_entities = [
            id_to_entity[rr["_id"]] for rr in reranked_raw if rr.get("_id") in id_to_entity
        ]

        # Fallback if ID mapping fails (should not happen in practice)
        if not reranked_entities:
            reranked_entities = entities

        return reranked_entities[: query.limit]
