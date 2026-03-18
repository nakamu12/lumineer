"""Unit tests for MCP server tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_search_result(hits: int = 2) -> MagicMock:
    """Return a mock SearchResult with `hits` courses."""
    result = MagicMock()
    result.total_hits = hits
    result.formatted_context = "course1, course2"

    courses = []
    for i in range(hits):
        c = MagicMock()
        c.title = f"Course {i}"
        c.organization = "TestOrg"
        c.level = "Beginner" if i % 2 == 0 else "Intermediate"
        c.rating = 4.5
        c.skills = ["Python", "ML"]
        courses.append(c)

    result.courses = courses
    return result


def _patch_usecase(hits: int = 2):
    """Context manager that patches SearchCoursesUseCase.execute."""
    mock_result = _make_search_result(hits)
    mock_usecase = MagicMock()
    mock_usecase.execute = AsyncMock(return_value=mock_result)
    return mock_usecase, mock_result


# ---------------------------------------------------------------------------
# ask_course_finder tests
# ---------------------------------------------------------------------------


class TestAskCourseFinder:
    """Tests for the ask_course_finder MCP tool."""

    @pytest.mark.asyncio
    async def test_returns_agent_final_output(self) -> None:
        """ask_course_finder should return the Triage Agent's final output."""
        from app.interfaces.mcp.server import ask_course_finder

        mock_result = MagicMock()
        mock_result.final_output = "Here are the top Python courses for you."

        with (
            patch("app.interfaces.mcp.server.create_triage_agent") as mock_create,
            patch("app.interfaces.mcp.server.Runner") as mock_runner,
            patch("app.interfaces.mcp.server.get_settings") as mock_settings,
        ):
            mock_settings.return_value.AGENT_MAX_TURNS = 10
            mock_runner.run = AsyncMock(return_value=mock_result)

            result = await ask_course_finder("Python courses for beginners")

        assert "Python courses" in result or "Python" in result
        mock_runner.run.assert_called_once()
        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_query_to_agent(self) -> None:
        """ask_course_finder should pass the query to Runner.run."""
        from app.interfaces.mcp.server import ask_course_finder

        mock_result = MagicMock()
        mock_result.final_output = "Result"

        with (
            patch("app.interfaces.mcp.server.create_triage_agent"),
            patch("app.interfaces.mcp.server.Runner") as mock_runner,
            patch("app.interfaces.mcp.server.get_settings") as mock_settings,
        ):
            mock_settings.return_value.AGENT_MAX_TURNS = 10
            mock_runner.run = AsyncMock(return_value=mock_result)

            await ask_course_finder("learn deep learning in 3 months")

        call_kwargs = mock_runner.run.call_args
        assert call_kwargs.kwargs.get("input") == "learn deep learning in 3 months"

    @pytest.mark.asyncio
    async def test_returns_string_on_error(self) -> None:
        """ask_course_finder should return an error string on unexpected failure."""
        from app.interfaces.mcp.server import ask_course_finder

        with (
            patch("app.interfaces.mcp.server.create_triage_agent"),
            patch("app.interfaces.mcp.server.Runner") as mock_runner,
            patch("app.interfaces.mcp.server.get_settings") as mock_settings,
        ):
            mock_settings.return_value.AGENT_MAX_TURNS = 10
            mock_runner.run = AsyncMock(side_effect=RuntimeError("network error"))

            result = await ask_course_finder("any query")

        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# search_courses_mcp tests
# ---------------------------------------------------------------------------


class TestSearchCoursesMcp:
    """Tests for the search_courses MCP tool."""

    @pytest.mark.asyncio
    async def test_returns_formatted_context(self) -> None:
        """search_courses should return the formatted course context."""
        from app.interfaces.mcp.server import search_courses_mcp

        mock_usecase, mock_result = _patch_usecase(hits=2)

        with (
            patch("app.interfaces.mcp.server.get_container"),
            patch("app.interfaces.mcp.server.get_settings") as mock_settings,
            patch(
                "app.interfaces.mcp.server.SearchCoursesUseCase",
                return_value=mock_usecase,
            ),
            patch("app.interfaces.mcp.server.create_reranker"),
            patch("app.interfaces.mcp.server.create_formatter"),
        ):
            mock_settings.return_value.RERANKER_STRATEGY = "none"
            mock_settings.return_value.CONTEXT_FORMAT = "json"
            mock_settings.return_value.SIMILARITY_THRESHOLD = 0.7

            result = await search_courses_mcp(query="machine learning")

        assert result == "course1, course2"

    @pytest.mark.asyncio
    async def test_passes_filters_to_use_case(self) -> None:
        """search_courses should forward level/org/rating/skills to SearchQuery."""
        from app.interfaces.mcp.server import search_courses_mcp

        mock_usecase, _ = _patch_usecase()

        with (
            patch("app.interfaces.mcp.server.get_container"),
            patch("app.interfaces.mcp.server.get_settings") as mock_settings,
            patch(
                "app.interfaces.mcp.server.SearchCoursesUseCase",
                return_value=mock_usecase,
            ),
            patch("app.interfaces.mcp.server.create_reranker"),
            patch("app.interfaces.mcp.server.create_formatter"),
            patch("app.interfaces.mcp.server.SearchQuery") as mock_query_cls,
        ):
            mock_settings.return_value.RERANKER_STRATEGY = "none"
            mock_settings.return_value.CONTEXT_FORMAT = "json"
            mock_settings.return_value.SIMILARITY_THRESHOLD = 0.7

            await search_courses_mcp(
                query="Python",
                level="Beginner",
                organization="Stanford",
                min_rating=4.0,
                skills=["Python", "ML"],
                limit=5,
            )

        mock_query_cls.assert_called_once()
        call_kwargs = mock_query_cls.call_args.kwargs
        assert call_kwargs["level"] == "Beginner"
        assert call_kwargs["organization"] == "Stanford"
        assert call_kwargs["min_rating"] == 4.0
        assert call_kwargs["skills"] == ["Python", "ML"]
        assert call_kwargs["limit"] == 5

    @pytest.mark.asyncio
    async def test_no_results_returns_helpful_message(self) -> None:
        """search_courses should return a helpful message when no courses found."""
        from app.interfaces.mcp.server import search_courses_mcp

        mock_usecase, _ = _patch_usecase(hits=0)

        with (
            patch("app.interfaces.mcp.server.get_container"),
            patch("app.interfaces.mcp.server.get_settings") as mock_settings,
            patch(
                "app.interfaces.mcp.server.SearchCoursesUseCase",
                return_value=mock_usecase,
            ),
            patch("app.interfaces.mcp.server.create_reranker"),
            patch("app.interfaces.mcp.server.create_formatter"),
        ):
            mock_settings.return_value.RERANKER_STRATEGY = "none"
            mock_settings.return_value.CONTEXT_FORMAT = "json"
            mock_settings.return_value.SIMILARITY_THRESHOLD = 0.7

            result = await search_courses_mcp(query="obscure topic xyz")

        assert isinstance(result, str)
        assert "No courses" in result or "no courses" in result.lower()


# ---------------------------------------------------------------------------
# get_skill_gap_mcp tests
# ---------------------------------------------------------------------------


class TestGetSkillGapMcp:
    """Tests for the get_skill_gap MCP tool."""

    @pytest.mark.asyncio
    async def test_returns_skill_gap_analysis(self) -> None:
        """get_skill_gap should return a formatted skill gap analysis string."""
        from app.interfaces.mcp.server import get_skill_gap_mcp

        mock_usecase, _ = _patch_usecase(hits=2)

        with (
            patch("app.interfaces.mcp.server.get_container"),
            patch("app.interfaces.mcp.server.get_settings") as mock_settings,
            patch(
                "app.interfaces.mcp.server.SearchCoursesUseCase",
                return_value=mock_usecase,
            ),
            patch("app.interfaces.mcp.server.create_reranker"),
            patch("app.interfaces.mcp.server.create_formatter"),
        ):
            mock_settings.return_value.RERANKER_STRATEGY = "none"
            mock_settings.return_value.CONTEXT_FORMAT = "json"
            mock_settings.return_value.SIMILARITY_THRESHOLD = 0.7

            result = await get_skill_gap_mcp(
                target_role="Data Scientist",
                current_skills=["Python", "SQL"],
            )

        assert isinstance(result, str)
        assert "Data Scientist" in result

    @pytest.mark.asyncio
    async def test_identifies_missing_skills(self) -> None:
        """get_skill_gap should identify skills not in current_skills."""
        from app.interfaces.mcp.server import get_skill_gap_mcp

        mock_result = _make_search_result(hits=1)
        mock_result.courses[0].skills = ["Python", "TensorFlow", "Deep Learning"]
        mock_usecase = MagicMock()
        mock_usecase.execute = AsyncMock(return_value=mock_result)

        with (
            patch("app.interfaces.mcp.server.get_container"),
            patch("app.interfaces.mcp.server.get_settings") as mock_settings,
            patch(
                "app.interfaces.mcp.server.SearchCoursesUseCase",
                return_value=mock_usecase,
            ),
            patch("app.interfaces.mcp.server.create_reranker"),
            patch("app.interfaces.mcp.server.create_formatter"),
        ):
            mock_settings.return_value.RERANKER_STRATEGY = "none"
            mock_settings.return_value.CONTEXT_FORMAT = "json"
            mock_settings.return_value.SIMILARITY_THRESHOLD = 0.7

            result = await get_skill_gap_mcp(
                target_role="ML Engineer",
                current_skills=["Python"],
            )

        # TensorFlow and Deep Learning should appear as skills to acquire
        assert "TensorFlow" in result or "tensorflow" in result.lower()


# ---------------------------------------------------------------------------
# get_learning_path_mcp tests
# ---------------------------------------------------------------------------


class TestGetLearningPathMcp:
    """Tests for the get_learning_path MCP tool."""

    @pytest.mark.asyncio
    async def test_returns_path_with_levels(self) -> None:
        """get_learning_path should return courses grouped by level."""
        from app.interfaces.mcp.server import get_learning_path_mcp

        mock_usecase, _ = _patch_usecase(hits=2)

        with (
            patch("app.interfaces.mcp.server.get_container"),
            patch("app.interfaces.mcp.server.get_settings") as mock_settings,
            patch(
                "app.interfaces.mcp.server.SearchCoursesUseCase",
                return_value=mock_usecase,
            ),
            patch("app.interfaces.mcp.server.create_reranker"),
            patch("app.interfaces.mcp.server.create_formatter"),
        ):
            mock_settings.return_value.RERANKER_STRATEGY = "none"
            mock_settings.return_value.CONTEXT_FORMAT = "json"
            mock_settings.return_value.SIMILARITY_THRESHOLD = 0.7

            result = await get_learning_path_mcp(
                goal="Become a web developer",
                timeframe="3 months",
            )

        assert isinstance(result, str)
        assert "web developer" in result.lower() or "Learning Path" in result

    @pytest.mark.asyncio
    async def test_includes_timeframe_and_skills(self) -> None:
        """get_learning_path should include timeframe and current_skills in output."""
        from app.interfaces.mcp.server import get_learning_path_mcp

        mock_usecase, _ = _patch_usecase(hits=1)

        with (
            patch("app.interfaces.mcp.server.get_container"),
            patch("app.interfaces.mcp.server.get_settings") as mock_settings,
            patch(
                "app.interfaces.mcp.server.SearchCoursesUseCase",
                return_value=mock_usecase,
            ),
            patch("app.interfaces.mcp.server.create_reranker"),
            patch("app.interfaces.mcp.server.create_formatter"),
        ):
            mock_settings.return_value.RERANKER_STRATEGY = "none"
            mock_settings.return_value.CONTEXT_FORMAT = "json"
            mock_settings.return_value.SIMILARITY_THRESHOLD = 0.7

            result = await get_learning_path_mcp(
                goal="Learn React",
                current_skills=["JavaScript"],
                timeframe="6 weeks",
            )

        assert "6 weeks" in result
        assert "JavaScript" in result
