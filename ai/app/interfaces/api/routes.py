"""Litestar API route definitions."""

from __future__ import annotations

from dataclasses import dataclass

from litestar import Litestar, get, post
from litestar.config.cors import CORSConfig
from litestar.exceptions import HTTPException

from app.config.container import build_container, get_container
from app.config.settings import get_settings
from app.domain.usecases.search_courses import SearchCoursesUseCase, SearchQuery, SearchResult
from app.infrastructure.formatters import create_formatter
from app.infrastructure.reranking import create_reranker

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


@dataclass
class SearchRequest:
    query: str
    level: str | None = None
    organization: str | None = None
    min_rating: float | None = None
    skills: list[str] | None = None
    limit: int = 10
    threshold: float | None = None
    reranker: str | None = None
    formatter: str | None = None


@dataclass
class CourseResponse:
    id: str
    title: str
    organization: str
    level: str | None
    rating: float
    enrolled: int
    skills: list[str]
    url: str
    description: str
    schedule: str | None
    instructor: str | None


@dataclass
class SearchResponse:
    courses: list[CourseResponse]
    formatted_context: str
    total_hits: int
    reranker_applied: str
    formatter_applied: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "ok",
        "service": "lumineer-ai",
        "env": settings.APP_ENV,
    }


@post("/search")
async def search_courses(data: SearchRequest) -> SearchResponse:
    """
    Hybrid RAG search endpoint.

    Reranker and formatter can be overridden per-request; defaults come
    from environment variables (RERANKER_STRATEGY / CONTEXT_FORMAT).
    """
    settings = get_settings()
    container = get_container()

    reranker_strategy = data.reranker or settings.RERANKER_STRATEGY
    formatter_format = data.formatter or settings.CONTEXT_FORMAT

    try:
        reranker = create_reranker(reranker_strategy)
        formatter = create_formatter(formatter_format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    usecase = SearchCoursesUseCase(
        vector_store=container.vector_store,
        embedding=container.embedding,
        reranker=reranker,
        formatter=formatter,
    )

    query = SearchQuery(
        query=data.query,
        level=data.level,
        organization=data.organization,
        min_rating=data.min_rating,
        skills=data.skills,
        limit=data.limit,
        threshold=data.threshold if data.threshold is not None else settings.SIMILARITY_THRESHOLD,
    )

    result: SearchResult = await usecase.execute(query)

    return SearchResponse(
        courses=[
            CourseResponse(
                id=c.id,
                title=c.title,
                organization=c.organization,
                level=c.level,
                rating=c.rating,
                enrolled=c.enrolled,
                skills=c.skills,
                url=c.url,
                description=c.description,
                schedule=c.schedule,
                instructor=c.instructor,
            )
            for c in result.courses
        ],
        formatted_context=result.formatted_context,
        total_hits=result.total_hits,
        reranker_applied=result.reranker_applied,
        formatter_applied=result.formatter_applied,
    )


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> Litestar:
    """Create and configure the Litestar application."""
    cors_config = CORSConfig(allow_origins=["*"])

    # Wire up DI container at startup
    build_container()

    return Litestar(
        route_handlers=[health_check, search_courses],
        cors_config=cors_config,
    )
