"""Litestar API route definitions."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from agents import ItemHelpers, Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from litestar import Litestar, get, post
from litestar.config.cors import CORSConfig
from litestar.exceptions import HTTPException
from litestar.response import Stream

from app.agents import create_triage_agent
from app.config.container import build_container, get_container
from app.config.settings import get_settings
from app.domain.usecases.search_courses import SearchCoursesUseCase, SearchQuery, SearchResult
from app.infrastructure.formatters import create_formatter
from app.infrastructure.reranking import create_reranker

logger = logging.getLogger(__name__)

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


@dataclass
class ChatRequest:
    message: str
    session_id: str | None = None


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
async def search_courses_endpoint(data: SearchRequest) -> SearchResponse:
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


def _sse_event(event_type: str, content: str) -> str:
    """Format a single SSE event line."""
    payload = json.dumps({"type": event_type, "content": content})
    return f"data: {payload}\n\n"


async def _stream_agent_response(message: str) -> AsyncGenerator[str, None]:
    """Run the Triage Agent and yield SSE events."""
    settings = get_settings()

    try:
        triage = create_triage_agent()
        result = Runner.run_streamed(
            triage,
            input=message,
            max_turns=settings.AGENT_MAX_TURNS,
        )

        async for event in result.stream_events():
            if event.type == "raw_response_event":
                continue

            if event.type == "agent_updated_stream_event":
                yield _sse_event("handoff", event.new_agent.name)

            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    tool_name = getattr(event.item.raw_item, "name", None) or "unknown"
                    yield _sse_event("tool_call", tool_name)
                elif event.item.type == "tool_call_output_item":
                    yield _sse_event("tool_result", str(event.item.output)[:200])
                elif event.item.type == "message_output_item":
                    text = ItemHelpers.text_message_output(event.item)
                    yield _sse_event("text_delta", text)

        yield _sse_event("done", "")

    except InputGuardrailTripwireTriggered:
        yield _sse_event(
            "error",
            "Your message was blocked by our safety filters. Please rephrase and try again.",
        )
    except Exception:
        logger.exception("Agent chat error")
        yield _sse_event("error", "An unexpected error occurred. Please try again.")


@post("/agents/chat")
async def agent_chat(data: ChatRequest) -> Stream:
    """Chat endpoint: runs Triage Agent with SSE streaming."""
    return Stream(
        _stream_agent_response(data.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> Litestar:
    """Create and configure the Litestar application."""
    cors_config = CORSConfig(allow_origins=["*"])

    # Ensure Agents SDK can read the API key from environment
    settings = get_settings()
    os.environ.setdefault("OPENAI_API_KEY", settings.OPENAI_API_KEY)

    # Wire up DI container at startup
    build_container()

    return Litestar(
        route_handlers=[health_check, search_courses_endpoint, agent_chat],
        cors_config=cors_config,
    )
