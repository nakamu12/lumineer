"""analyze_skill_gap tool for the Skill Gap Agent."""

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
async def analyze_skill_gap(
    target_role: str,
    current_skills: list[str] | None = None,
    level: str | None = None,
    limit: int = 10,
) -> str:
    """Analyze the skill gap between current skills and a target role or career goal.

    Searches for courses related to the target role, extracts required skills,
    and identifies which skills the user is missing.

    Args:
        target_role: The career goal or target role (e.g., "Data Scientist", "Web Developer").
        current_skills: List of skills the user already has (e.g., ["Python", "SQL"]).
        level: Optional course difficulty filter — "Beginner", "Intermediate", or "Advanced".
        limit: Maximum number of relevant courses to return (default 10).
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
            query=f"skills and courses for {target_role}",
            level=level,
            limit=limit,
            threshold=settings.SIMILARITY_THRESHOLD,
        )

        result = await usecase.execute(search_query)

        if result.total_hits == 0:
            return (
                f"No courses found for the role '{target_role}'. "
                "Try a different role name or broader description."
            )

        # Extract all skills from found courses
        all_required_skills: set[str] = set()
        for course in result.courses:
            for skill in course.skills:
                all_required_skills.add(skill)

        user_skills = {s.strip().lower() for s in (current_skills or [])}
        required_lower = {s.lower(): s for s in all_required_skills}
        missing = {required_lower[s] for s in required_lower if s not in user_skills}
        already_have = {required_lower[s] for s in required_lower if s in user_skills}

        lines: list[str] = []
        lines.append(f"=== Skill Gap Analysis for: {target_role} ===")
        lines.append("")
        have_str = ", ".join(sorted(already_have)) or "None identified"
        lines.append(f"Skills you already have ({len(already_have)}): {have_str}")
        miss_str = ", ".join(sorted(missing)) or "None — you have all identified skills!"
        lines.append(f"Skills to acquire ({len(missing)}): {miss_str}")
        lines.append("")
        lines.append("--- Relevant Courses ---")
        lines.append(result.formatted_context)

        return "\n".join(lines)

    except Exception:
        logger.exception("analyze_skill_gap tool failed")
        return "An error occurred while analyzing skill gaps. Please try again."
