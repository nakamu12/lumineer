"""Tests for the generate_learning_path tool function."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents.tool_context import ToolContext
from agents.usage import Usage

from app.tools.generate_learning_path import generate_learning_path


def _make_hit(
    title: str = "Test Course",
    level: str = "Beginner",
    **overrides: Any,
) -> dict[str, Any]:
    """Create a minimal Qdrant hit dict."""
    base: dict[str, Any] = {
        "_id": "test-id-1",
        "_score": 0.85,
        "title": title,
        "description": "A great course",
        "skills": ["Python", "ML"],
        "level": level,
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


def _make_ctx(args: dict[str, Any]) -> ToolContext[None]:
    """Create a minimal ToolContext for testing."""
    args_json = json.dumps(args)
    return ToolContext(
        context=None,
        usage=Usage(),
        tool_name="generate_learning_path",
        tool_call_id="test-call-id",
        tool_arguments=args_json,
    )


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
    hits = [
        _make_hit("Python Basics", "Beginner", _id="id-1"),
        _make_hit("ML Foundations", "Intermediate", _id="id-2"),
        _make_hit("Deep Learning", "Advanced", _id="id-3"),
    ]

    mock_vs = AsyncMock()
    mock_vs.hybrid_search.return_value = hits

    mock_emb = AsyncMock()
    mock_emb.embed.return_value = [0.1] * 3072

    container = MagicMock()
    container.vector_store = mock_vs
    container.embedding = mock_emb

    return container


class TestGenerateLearningPathTool:
    @pytest.mark.asyncio
    async def test_returns_learning_path(self, mock_container: Any) -> None:
        args = {"goal": "learn machine learning"}
        ctx = _make_ctx(args)
        with patch(
            "app.tools.generate_learning_path.get_container",
            return_value=mock_container,
        ):
            result = await generate_learning_path.on_invoke_tool(ctx, json.dumps(args))
            assert isinstance(result, str)
            assert "Learning Path Data" in result

    @pytest.mark.asyncio
    async def test_groups_by_level(self, mock_container: Any) -> None:
        args = {"goal": "learn machine learning"}
        ctx = _make_ctx(args)
        with patch(
            "app.tools.generate_learning_path.get_container",
            return_value=mock_container,
        ):
            result = await generate_learning_path.on_invoke_tool(ctx, json.dumps(args))
            assert "[Beginner]" in result
            assert "[Intermediate]" in result
            assert "[Advanced]" in result

    @pytest.mark.asyncio
    async def test_includes_timeframe(self, mock_container: Any) -> None:
        args = {"goal": "learn machine learning", "timeframe": "3 months"}
        ctx = _make_ctx(args)
        with patch(
            "app.tools.generate_learning_path.get_container",
            return_value=mock_container,
        ):
            result = await generate_learning_path.on_invoke_tool(ctx, json.dumps(args))
            assert "3 months" in result

    @pytest.mark.asyncio
    async def test_no_results_message(self, mock_container: Any) -> None:
        mock_container.vector_store.hybrid_search.return_value = []

        args = {"goal": "nonexistent topic xyz"}
        ctx = _make_ctx(args)
        with patch(
            "app.tools.generate_learning_path.get_container",
            return_value=mock_container,
        ):
            result = await generate_learning_path.on_invoke_tool(ctx, json.dumps(args))
            assert "No courses found" in result

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_container: Any) -> None:
        mock_container.vector_store.hybrid_search.side_effect = RuntimeError("connection lost")

        args = {"goal": "learn Python"}
        ctx = _make_ctx(args)
        with patch(
            "app.tools.generate_learning_path.get_container",
            return_value=mock_container,
        ):
            result = await generate_learning_path.on_invoke_tool(ctx, json.dumps(args))
            assert "error" in result.lower() or "try again" in result.lower()
