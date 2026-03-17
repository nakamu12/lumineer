"""Litestar API route definitions."""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from agents import ItemHelpers, Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from litestar import Litestar, Response, get, post
from litestar.config.cors import CORSConfig
from litestar.exceptions import HTTPException
from litestar.response import Stream
from prometheus_client import generate_latest

from app.agents import create_triage_agent
from app.config.container import build_container, get_container
from app.config.settings import get_settings
from app.domain.usecases.get_course_detail import CourseNotFoundError, GetCourseDetailUseCase
from app.domain.usecases.search_courses import SearchCoursesUseCase, SearchQuery, SearchResult
from app.guardrails.input.pii_sanitizer import mask_pii
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
    modules: str | None = None


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


@get("/metrics")
async def metrics_endpoint() -> Response[bytes]:
    """Expose Prometheus metrics for scraping."""
    from app.observability.metrics import REGISTRY

    body = generate_latest(REGISTRY)
    return Response(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")


@post("/search")
async def search_courses_endpoint(data: SearchRequest) -> SearchResponse:
    """
    Hybrid RAG search endpoint.

    Reranker and formatter can be overridden per-request; defaults come
    from environment variables (RERANKER_STRATEGY / CONTEXT_FORMAT).
    """
    start = time.monotonic()
    settings = get_settings()
    container = get_container()
    metrics = container.metrics

    reranker_strategy = data.reranker or settings.RERANKER_STRATEGY
    formatter_format = data.formatter or settings.CONTEXT_FORMAT

    try:
        reranker = create_reranker(reranker_strategy)
        formatter = create_formatter(formatter_format)
    except ValueError as exc:
        metrics.record_request_error(endpoint="/search", method="POST")
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

    try:
        result: SearchResult = await usecase.execute(query)
    except Exception:
        metrics.record_request_error(endpoint="/search", method="POST")
        raise
    finally:
        duration = time.monotonic() - start
        metrics.record_request_duration(endpoint="/search", method="POST", duration=duration)

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
                modules=c.modules,
            )
            for c in result.courses
        ],
        formatted_context=result.formatted_context,
        total_hits=result.total_hits,
        reranker_applied=result.reranker_applied,
        formatter_applied=result.formatter_applied,
    )


@get("/courses/{course_id:str}")
async def get_course_detail(course_id: str) -> CourseResponse:
    """Retrieve a single course by its Qdrant point ID."""
    start = time.monotonic()
    container = get_container()
    metrics = container.metrics

    try:
        usecase = GetCourseDetailUseCase(vector_store=container.vector_store)
        course = await usecase.execute(course_id)
    except CourseNotFoundError as exc:
        metrics.record_request_error(endpoint="/courses/{id}", method="GET")
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        metrics.record_request_error(endpoint="/courses/{id}", method="GET")
        raise
    finally:
        duration = time.monotonic() - start
        metrics.record_request_duration(endpoint="/courses/{id}", method="GET", duration=duration)

    return CourseResponse(
        id=course.id,
        title=course.title,
        organization=course.organization,
        level=course.level,
        rating=course.rating,
        enrolled=course.enrolled,
        skills=course.skills,
        url=course.url,
        description=course.description,
        schedule=course.schedule,
        instructor=course.instructor,
        modules=course.modules,
    )


def _sse_event(event_type: str, content: str) -> str:
    """Format a single SSE event line."""
    payload = json.dumps({"type": event_type, "content": content})
    return f"data: {payload}\n\n"


async def _stream_agent_response(message: str) -> AsyncGenerator[str, None]:
    """Run the Triage Agent and yield SSE events.

    PII in the user message is masked before sending to the agent.
    The PII mappings are stored for restoration in Issue #62 (pii_restorer).
    """
    start = time.monotonic()
    settings = get_settings()
    container = get_container()
    metrics = container.metrics
    tracer = container.tracer
    token_tracker = container.token_tracker
    previous_agent_name = "Triage Agent"

    # Create a Langfuse trace for this chat request
    trace = tracer.create_trace(name="agent-chat")

    try:
        # L1 Guard: Mask PII before agent processing
        pii_result = mask_pii(message)
        masked_message = pii_result.masked_text
        # pii_result.mappings will be used by pii_restorer in Issue #62

        triage = create_triage_agent()
        result = Runner.run_streamed(
            triage,
            input=masked_message,
            max_turns=settings.AGENT_MAX_TURNS,
        )

        async for event in result.stream_events():
            if event.type == "raw_response_event":
                continue

            if event.type == "agent_updated_stream_event":
                new_agent_name = event.new_agent.name
                metrics.record_agent_handoff(
                    from_agent=previous_agent_name, to_agent=new_agent_name
                )
                previous_agent_name = new_agent_name
                yield _sse_event("handoff", new_agent_name)

            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    tool_name = getattr(event.item.raw_item, "name", None) or "unknown"
                    yield _sse_event("tool_call", tool_name)
                elif event.item.type == "tool_call_output_item":
                    yield _sse_event("tool_result", "completed")
                elif event.item.type == "message_output_item":
                    text = ItemHelpers.text_message_output(event.item)
                    yield _sse_event("text_delta", text)

        # Record token usage and LLM metrics from the completed run
        llm_duration = time.monotonic() - start
        metrics.record_llm_request(agent=previous_agent_name, status="success")
        metrics.record_llm_latency(agent=previous_agent_name, duration=llm_duration)

        usage = getattr(result, "usage", None)
        if usage is not None:
            input_tok = getattr(usage, "input_tokens", 0)
            output_tok = getattr(usage, "output_tokens", 0)
            token_tracker.track(
                input_tokens=input_tok,
                output_tokens=output_tok,
                model=settings.AGENT_MODEL,
                trace=trace,
                generation_name="agent-chat",
            )
            # Estimate cost (GPT-4o-mini: $0.15/1M input, $0.60/1M output)
            cost = (input_tok * 0.15 + output_tok * 0.60) / 1_000_000
            metrics.record_llm_cost(model=settings.AGENT_MODEL, cost_usd=cost)

        yield _sse_event("done", "")

    except InputGuardrailTripwireTriggered:
        metrics.record_llm_request(agent=previous_agent_name, status="error")
        metrics.record_guardrail_trigger(guardrail_type="input_tripwire")
        metrics.record_request_error(endpoint="/agents/chat", method="POST")
        yield _sse_event(
            "error",
            "Your message was blocked by our safety filters. Please rephrase and try again.",
        )
    except Exception:
        logger.exception("Agent chat error")
        metrics.record_llm_request(agent=previous_agent_name, status="error")
        metrics.record_request_error(endpoint="/agents/chat", method="POST")
        yield _sse_event("error", "An unexpected error occurred. Please try again.")
    finally:
        duration = time.monotonic() - start
        metrics.record_request_duration(endpoint="/agents/chat", method="POST", duration=duration)
        tracer.flush()


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

    # Wire up DI container (including observability) at startup
    build_container()

    return Litestar(
        route_handlers=[
            health_check,
            metrics_endpoint,
            search_courses_endpoint,
            get_course_detail,
            agent_chat,
        ],
        cors_config=cors_config,
    )
