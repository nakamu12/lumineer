"""MCP Server — Lumineer Course Finder.

Exposes four tools over the Streamable HTTP transport:

  ask_course_finder     — natural language query via Triage Agent
  search_courses_mcp    — filter-based hybrid RAG search
  get_skill_gap_mcp     — skill gap analysis for a target role
  get_learning_path_mcp — learning path generation

When KEYCLOAK_URL is set and MCP_REQUIRE_AUTH=true, the FastMCP server is
configured with OAuth 2.1 token validation against Keycloak.  In dev mode
(KEYCLOAK_URL unset) all requests pass through without auth.

Architecture note: tool functions are defined as plain async functions and
registered via FastMCP.add_tool() so they can be tested independently.
"""

from __future__ import annotations

import logging
from typing import Any

import jwt
from agents import Runner
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

from app.agents import create_triage_agent
from app.config.container import get_container
from app.config.settings import get_settings
from app.domain.usecases.search_courses import SearchCoursesUseCase, SearchQuery
from app.infrastructure.formatters import create_formatter
from app.infrastructure.reranking import create_reranker
from app.interfaces.mcp.auth import JWTValidator, create_jwt_validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Token verifier (Resource Server role for Keycloak OAuth 2.1)
# ---------------------------------------------------------------------------


class KeycloakTokenVerifier(TokenVerifier):
    """Validates MCP Bearer tokens against Keycloak's JWKS endpoint."""

    def __init__(self, jwt_validator: JWTValidator) -> None:
        self._validator = jwt_validator

    async def verify_token(self, token: str) -> AccessToken | None:
        """Return an AccessToken if *token* is valid, None otherwise."""
        try:
            claims = self._validator.validate(token)
            return AccessToken(
                token=token,
                client_id=claims.get("azp") or claims.get("client_id") or "unknown",
                scopes=claims.get("scope", "").split(),
                expires_at=claims.get("exp"),
                resource=claims.get("aud"),
            )
        except (jwt.InvalidTokenError, jwt.PyJWKClientError) as exc:
            logger.debug("Token verification failed: %s", exc)
            return None


# ---------------------------------------------------------------------------
# Tool helpers
# ---------------------------------------------------------------------------


async def _run_search(
    query: str,
    level: str | None = None,
    organization: str | None = None,
    min_rating: float | None = None,
    skills: list[str] | None = None,
    limit: int = 10,
) -> Any:
    """Execute SearchCoursesUseCase and return the result."""
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

    return await usecase.execute(search_query)


# ---------------------------------------------------------------------------
# Tool functions (plain async — registered on FastMCP via add_tool)
# ---------------------------------------------------------------------------


async def ask_course_finder(query: str) -> str:
    """Run the Triage Agent on an open-ended natural language query.

    Args:
        query: Any course-related question in natural language.
            Examples:
            - "Find Python courses for beginners"
            - "What skills do I need to become a data scientist?"
            - "Build me a 3-month plan to learn web development"

    Returns:
        Agent response with course recommendations, skill analysis, or
        a learning path depending on the query intent.
    """
    try:
        settings = get_settings()
        triage = create_triage_agent()
        result = await Runner.run(
            triage,
            input=query,
            max_turns=settings.AGENT_MAX_TURNS,
        )
        return str(result.final_output)
    except Exception:
        logger.exception("ask_course_finder failed")
        return "An error occurred while processing your request. Please try again."


async def search_courses_mcp(
    query: str,
    level: str | None = None,
    organization: str | None = None,
    min_rating: float | None = None,
    skills: list[str] | None = None,
    limit: int = 10,
) -> str:
    """Search courses with optional structured filters.

    Args:
        query: Search query — keyword or natural language description.
        level: Difficulty filter — "Beginner", "Intermediate", or "Advanced".
        organization: Provider filter (e.g., "Stanford", "Google", "DeepLearning.AI").
        min_rating: Minimum course rating between 0.0 and 5.0.
        skills: Required skills (e.g., ["Python", "Machine Learning"]).
        limit: Maximum number of results to return (default 10, max 100).

    Returns:
        Formatted list of matching courses with title, org, level, rating,
        enrolled count, and skills.
    """
    try:
        result = await _run_search(
            query=query,
            level=level,
            organization=organization,
            min_rating=min_rating,
            skills=skills,
            limit=limit,
        )

        if result.total_hits == 0:
            return "No courses found matching your criteria. Try broadening your search."

        return str(result.formatted_context)

    except Exception:
        logger.exception("search_courses_mcp failed")
        return "An error occurred while searching for courses. Please try again."


async def get_skill_gap_mcp(
    target_role: str,
    current_skills: list[str] | None = None,
    level: str | None = None,
    limit: int = 10,
) -> str:
    """Identify skills required for a role that the user doesn't yet have.

    Args:
        target_role: Career goal or target role (e.g., "Data Scientist", "ML Engineer").
        current_skills: Skills the user already possesses (e.g., ["Python", "SQL"]).
        level: Preferred course difficulty — "Beginner", "Intermediate", or "Advanced".
        limit: Maximum number of courses to analyse for skill extraction (default 10).

    Returns:
        Analysis showing skills already acquired, skills to acquire, and
        a list of relevant courses to close the gap.
    """
    try:
        result = await _run_search(
            query=f"skills and courses for {target_role}",
            level=level,
            limit=limit,
        )

        if result.total_hits == 0:
            return (
                f"No courses found for the role '{target_role}'. "
                "Try a different role name or broader description."
            )

        # Extract all unique skills from the retrieved courses
        all_required_skills: set[str] = set()
        for course in result.courses:
            for skill in course.skills:
                all_required_skills.add(skill)

        user_skills_lower = {s.strip().lower() for s in (current_skills or [])}
        required_lower = {s.lower(): s for s in all_required_skills}
        missing = {required_lower[s] for s in required_lower if s not in user_skills_lower}
        already_have = {required_lower[s] for s in required_lower if s in user_skills_lower}

        lines: list[str] = [
            f"=== Skill Gap Analysis for: {target_role} ===",
            "",
            f"Skills you already have ({len(already_have)}): "
            + (", ".join(sorted(already_have)) or "None identified"),
            f"Skills to acquire ({len(missing)}): "
            + (", ".join(sorted(missing)) or "None — you have all identified skills!"),
            "",
            "--- Relevant Courses ---",
            result.formatted_context,
        ]

        return "\n".join(lines)

    except Exception:
        logger.exception("get_skill_gap_mcp failed")
        return "An error occurred while analyzing skill gaps. Please try again."


async def get_learning_path_mcp(
    goal: str,
    current_skills: list[str] | None = None,
    timeframe: str | None = None,
    limit: int = 15,
) -> str:
    """Create a step-by-step learning path toward a goal.

    Args:
        goal: Learning objective (e.g., "Become a web developer", "Learn machine learning").
        current_skills: Skills already possessed — used for context in the output.
        timeframe: Desired completion time (e.g., "3 months", "6 weeks").
        limit: Maximum number of courses to include in the path (default 15).

    Returns:
        Learning path with courses grouped by level (Beginner / Intermediate /
        Advanced / Unspecified) and full course details.
    """
    try:
        result = await _run_search(
            query=f"learning path courses for {goal}",
            limit=limit,
        )

        if result.total_hits == 0:
            return (
                f"No courses found for the goal '{goal}'. "
                "Try rephrasing your learning goal or using broader terms."
            )

        # Group courses by difficulty level
        by_level: dict[str, list[str]] = {
            "Beginner": [],
            "Intermediate": [],
            "Advanced": [],
            "Unspecified": [],
        }
        for course in result.courses:
            key = course.level if course.level in by_level else "Unspecified"
            by_level[key].append(
                f"  - {course.title} ({course.organization}, rating: {course.rating})"
            )

        lines: list[str] = [f"=== Learning Path Data for: {goal} ==="]
        if timeframe:
            lines.append(f"Target timeframe: {timeframe}")
        if current_skills:
            lines.append(f"Current skills: {', '.join(current_skills)}")
        lines.append(f"Total courses found: {result.total_hits}")
        lines.append("")
        lines.append("--- Courses by Level ---")

        for level_name in ("Beginner", "Intermediate", "Advanced", "Unspecified"):
            courses_at_level = by_level[level_name]
            if courses_at_level:
                lines.append(f"\n[{level_name}] ({len(courses_at_level)} courses)")
                lines.extend(courses_at_level)

        lines.extend(["", "--- Full Course Details ---", result.formatted_context])

        return "\n".join(lines)

    except Exception:
        logger.exception("get_learning_path_mcp failed")
        return "An error occurred while generating the learning path. Please try again."


# ---------------------------------------------------------------------------
# ASGI app factory
# ---------------------------------------------------------------------------

_TOOL_DESCRIPTIONS: dict[str, str] = {
    "ask_course_finder": (
        "Ask a natural language question about courses. "
        "The Triage Agent routes to Search, Skill Gap, or Path specialist. "
        "Use this for open-ended queries."
    ),
    "search_courses_mcp": (
        "Search Coursera courses with hybrid RAG (semantic + keyword). "
        "Supports filtering by level, organization, minimum rating, and skills."
    ),
    "get_skill_gap_mcp": (
        "Analyze the skill gap between current skills and a target role. "
        "Returns missing skills and relevant courses."
    ),
    "get_learning_path_mcp": (
        "Generate a structured learning path toward a goal. "
        "Courses are grouped by level (Beginner → Intermediate → Advanced)."
    ),
}


def create_mcp_asgi_app() -> Any:
    """Return the MCP server as an ASGI app (Starlette, Streamable HTTP).

    When KEYCLOAK_URL + MCP_REQUIRE_AUTH=true are configured, the server
    validates Bearer tokens via Keycloak and exposes the
    /.well-known/oauth-protected-resource/mcp metadata endpoint.

    In dev (KEYCLOAK_URL unset), tools are accessible without authentication.
    """
    settings = get_settings()

    # Build FastMCP kwargs — add OAuth 2.1 only when Keycloak is configured
    kwargs: dict[str, Any] = {
        "name": "Lumineer Course Finder",
        "instructions": (
            "You provide AI-powered course search, skill gap analysis, and "
            "learning path generation for Coursera courses (6,645 courses). "
            "Use the appropriate tool based on the user's intent."
        ),
    }

    if settings.KEYCLOAK_URL and settings.MCP_REQUIRE_AUTH:
        base = settings.KEYCLOAK_URL.rstrip("/")
        issuer_url = f"{base}/realms/{settings.KEYCLOAK_REALM}"
        resource_server_url = (
            settings.MCP_RESOURCE_SERVER_URL or f"http://{settings.HOST}:{settings.PORT}/mcp"
        )

        jwt_validator = create_jwt_validator(settings.KEYCLOAK_URL, settings.KEYCLOAK_REALM)
        kwargs["auth"] = AuthSettings(
            issuer_url=issuer_url,  # type: ignore[arg-type]
            resource_server_url=resource_server_url,  # type: ignore[arg-type]
        )
        kwargs["token_verifier"] = KeycloakTokenVerifier(jwt_validator)

        logger.info(
            "MCP OAuth 2.1 enabled — issuer: %s, resource: %s",
            issuer_url,
            resource_server_url,
        )
    else:
        logger.info("MCP server started without authentication (dev mode)")

    mcp = FastMCP(**kwargs)

    # Register tools (plain async functions → registered by reference)
    mcp.add_tool(ask_course_finder, description=_TOOL_DESCRIPTIONS["ask_course_finder"])
    mcp.add_tool(search_courses_mcp, description=_TOOL_DESCRIPTIONS["search_courses_mcp"])
    mcp.add_tool(get_skill_gap_mcp, description=_TOOL_DESCRIPTIONS["get_skill_gap_mcp"])
    mcp.add_tool(get_learning_path_mcp, description=_TOOL_DESCRIPTIONS["get_learning_path_mcp"])

    return mcp.streamable_http_app()
