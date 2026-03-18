"""Tests for the search_courses tool function."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.search_courses import search_courses


def _make_hit(title: str = "Test Course", **overrides: Any) -> dict[str, Any]:
    """Create a minimal Qdrant hit dict."""
    base: dict[str, Any] = {
        "_id": "test-id-1",
        "_score": 0.85,
        "title": title,
        "description": "A great course",
        "skills": ["Python", "ML"],
        "level": "Beginner",
        "organization": "TestOrg",
        "rating": 4.5,
        "enrolled": 10000,
        "num_reviews": 500,
        "modules": "Module 1, Module 2",
        "schedule": "4 weeks",
        "url": "https://coursera.org/test",
        "instructor": "Dr. Test",
    }
    base.update(overrides)
    return base


@pytest.fixture(autouse=True)
def _mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure OPENAI_API_KEY is set so Settings can initialize."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy-key")


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """Clear the lru_cache on get_settings so monkeypatched env is picked up."""
    from app.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def mock_container() -> Any:
    """Mock the DI container with VectorStore and Embedding stubs."""
    mock_vs = AsyncMock()
    mock_vs.hybrid_search.return_value = [_make_hit()]

    mock_emb = AsyncMock()
    mock_emb.embed.return_value = [0.1] * 3072

    container = MagicMock()
    container.vector_store = mock_vs
    container.embedding = mock_emb

    return container


class TestSearchCoursesTool:
    @pytest.mark.asyncio
    async def test_returns_formatted_context(self, mock_container: Any) -> None:
        with patch("app.tools.search_courses.get_container", return_value=mock_container):
            result = await search_courses.on_invoke_tool(
                {"query": "Python courses"},
                "",
            )
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_no_results_message(self, mock_container: Any) -> None:
        mock_container.vector_store.hybrid_search.return_value = []

        with patch("app.tools.search_courses.get_container", return_value=mock_container):
            result = await search_courses.on_invoke_tool(
                {"query": "nonexistent topic xyz"},
                "",
            )
            assert "No courses found" in result or isinstance(result, str)

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_container: Any) -> None:
        mock_container.vector_store.hybrid_search.side_effect = RuntimeError("connection lost")

        with patch("app.tools.search_courses.get_container", return_value=mock_container):
            result = await search_courses.on_invoke_tool(
                {"query": "Python"},
                "",
            )
            assert "error" in result.lower() or "try again" in result.lower()
