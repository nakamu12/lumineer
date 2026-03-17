"""Tests for GetCourseDetailUseCase."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.domain.entities.course import CourseEntity
from app.domain.usecases.get_course_detail import CourseNotFoundError, GetCourseDetailUseCase


def _make_payload(**overrides: Any) -> dict[str, Any]:
    """Create a minimal Qdrant payload dict for a course."""
    base: dict[str, Any] = {
        "_id": "course-123",
        "title": "Machine Learning",
        "description": "An introduction to ML",
        "skills": ["Python", "TensorFlow"],
        "level": "Beginner",
        "organization": "Stanford",
        "rating": 4.8,
        "enrolled": 50000,
        "num_reviews": 1200,
        "modules": "Module 1: Intro, Module 2: Linear Regression",
        "schedule": "11 weeks",
        "url": "https://coursera.org/learn/ml",
        "instructor": "Andrew Ng",
    }
    base.update(overrides)
    return base


class TestGetCourseDetailUseCase:
    @pytest.mark.asyncio
    async def test_returns_course_entity_when_found(self) -> None:
        mock_vs = AsyncMock()
        mock_vs.get_by_id.return_value = _make_payload()

        usecase = GetCourseDetailUseCase(vector_store=mock_vs)
        result = await usecase.execute("course-123")

        assert isinstance(result, CourseEntity)
        assert result.id == "course-123"
        assert result.title == "Machine Learning"
        assert result.organization == "Stanford"
        assert result.rating == 4.8
        assert result.skills == ["Python", "TensorFlow"]
        mock_vs.get_by_id.assert_awaited_once_with("course-123")

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(self) -> None:
        mock_vs = AsyncMock()
        mock_vs.get_by_id.return_value = None

        usecase = GetCourseDetailUseCase(vector_store=mock_vs)

        with pytest.raises(CourseNotFoundError, match="course-999"):
            await usecase.execute("course-999")

    @pytest.mark.asyncio
    async def test_handles_missing_optional_fields(self) -> None:
        mock_vs = AsyncMock()
        mock_vs.get_by_id.return_value = _make_payload(
            level=None,
            instructor=None,
            schedule=None,
            modules=None,
            num_reviews=None,
            skills=[],
        )

        usecase = GetCourseDetailUseCase(vector_store=mock_vs)
        result = await usecase.execute("course-123")

        assert result.level is None
        assert result.instructor is None
        assert result.schedule is None
        assert result.modules is None
        assert result.skills == []

    @pytest.mark.asyncio
    async def test_normalizes_level_string(self) -> None:
        mock_vs = AsyncMock()
        mock_vs.get_by_id.return_value = _make_payload(level="Intermediate level")

        usecase = GetCourseDetailUseCase(vector_store=mock_vs)
        result = await usecase.execute("course-123")

        assert result.level == "Intermediate"

    @pytest.mark.asyncio
    async def test_clamps_rating_to_valid_range(self) -> None:
        mock_vs = AsyncMock()
        mock_vs.get_by_id.return_value = _make_payload(rating=6.0)

        usecase = GetCourseDetailUseCase(vector_store=mock_vs)
        result = await usecase.execute("course-123")

        assert result.rating == 5.0
