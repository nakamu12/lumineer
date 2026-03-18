"""generate_learning_path tool for the Path Agent."""

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
async def generate_learning_path(
    goal: str,
    current_skills: list[str] | None = None,
    timeframe: str | None = None,
    limit: int = 15,
) -> str:
    """Search for courses to build a structured learning path toward a goal.

    Finds courses at different difficulty levels and returns them with metadata
    so the agent can organize them into a logical learning sequence.

    Args:
        goal: The learning goal (e.g., "become a ML engineer").
        current_skills: Skills the user already has, to avoid redundant beginner courses.
        timeframe: Optional timeframe for the plan (e.g., "3 months", "6 months").
        limit: Maximum number of courses to include (default 15 for path diversity).
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
            query=f"learning path courses for {goal}",
            limit=limit,
            threshold=settings.SIMILARITY_THRESHOLD,
        )

        result = await usecase.execute(search_query)

        if result.total_hits == 0:
            return (
                f"No courses found for the goal '{goal}'. "
                "Try rephrasing your learning goal or using broader terms."
            )

        # Group courses by level for path ordering
        by_level: dict[str, list[str]] = {
            "Beginner": [],
            "Intermediate": [],
            "Advanced": [],
            "Unspecified": [],
        }
        for course in result.courses:
            level_key = course.level if course.level in by_level else "Unspecified"
            by_level[level_key].append(
                f"  - {course.title} ({course.organization}, rating: {course.rating})"
            )

        lines: list[str] = []
        lines.append(f"=== Learning Path Data for: {goal} ===")
        if timeframe:
            lines.append(f"Target timeframe: {timeframe}")
        if current_skills:
            lines.append(f"Current skills: {', '.join(current_skills)}")
        lines.append(f"Total courses found: {result.total_hits}")
        lines.append("")

        lines.append("--- Courses by Level ---")
        for level_name in ("Beginner", "Intermediate", "Advanced", "Unspecified"):
            courses_in_level = by_level[level_name]
            if courses_in_level:
                lines.append(f"\n[{level_name}] ({len(courses_in_level)} courses)")
                lines.extend(courses_in_level)

        lines.append("")
        lines.append("--- Full Course Details ---")
        lines.append(result.formatted_context)

        return "\n".join(lines)

    except Exception:
        logger.exception("generate_learning_path tool failed")
        return "An error occurred while generating the learning path. Please try again."
