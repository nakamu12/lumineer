"""search_courses tool for the Search Agent."""

from __future__ import annotations

import logging

from agents import function_tool

from app.config.container import get_container
from app.config.settings import get_settings
from app.domain.usecases.search_courses import SearchCoursesUseCase, SearchQuery
from app.infrastructure.formatters import create_formatter
from app.infrastructure.reranking import create_reranker

logger = logging.getLogger(__name__)


@function_tool
async def search_courses(
    query: str,
    level: str | None = None,
    organization: str | None = None,
    min_rating: float | None = None,
    skills: list[str] | None = None,
    limit: int = 10,
) -> str:
    """Search for Coursera courses using semantic and keyword hybrid search.

    Args:
        query: Natural language search query describing what the user wants to learn.
        level: Course difficulty filter — "Beginner", "Intermediate", or "Advanced".
        organization: Filter by provider (e.g., "Stanford", "Google", "DeepLearning.AI").
        min_rating: Minimum course rating (0.0–5.0).
        skills: Filter by specific skills (e.g., ["Python", "Machine Learning"]).
        limit: Maximum number of results to return (default 10).
    """
    try:
        container = get_container()
        settings = get_settings()

        reranker = create_reranker(settings.RERANKER_STRATEGY)
        formatter = create_formatter(settings.CONTEXT_FORMAT)

        usecase = SearchCoursesUseCase(
            vector_store=container.vector_store,
            embedding=container.embedding,
            reranker=reranker,
            formatter=formatter,
        )

        search_query = SearchQuery(
            query=query,
            level=level,
            organization=organization,
            min_rating=min_rating,
            skills=skills,
            limit=limit,
            threshold=settings.SIMILARITY_THRESHOLD,
        )

        result = await usecase.execute(search_query)

        if result.total_hits == 0:
            return "No courses found matching your criteria. Try broadening your search."

        return result.formatted_context

    except Exception:
        logger.exception("search_courses tool failed")
        return "An error occurred while searching for courses. Please try again."
