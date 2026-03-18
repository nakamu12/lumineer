"""Tests for the analyze_skill_gap tool function."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents.tool_context import ToolContext
from agents.usage import Usage

from app.tools.analyze_skill_gap import analyze_skill_gap


def _make_hit(title: str = "Test Course", **overrides: Any) -> dict[str, Any]:
    """Create a minimal Qdrant hit dict."""
    base: dict[str, Any] = {
        "_id": "test-id-1",
        "_score": 0.85,
        "title": title,
        "description": "A great course for data science",
        "skills": ["Python", "Machine Learning", "Statistics"],
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


def _make_ctx(args: dict[str, Any]) -> ToolContext[None]:
    """Create a minimal ToolContext for testing."""
    args_json = json.dumps(args)
    return ToolContext(
        context=None,
        usage=Usage(),
        tool_name="analyze_skill_gap",
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
    mock_vs = AsyncMock()
    mock_vs.hybrid_search.return_value = [_make_hit()]

    mock_emb = AsyncMock()
    mock_emb.embed.return_value = [0.1] * 3072

    container = MagicMock()
    container.vector_store = mock_vs
    container.embedding = mock_emb

    return container


class TestAnalyzeSkillGapTool:
    @pytest.mark.asyncio
    async def test_returns_skill_gap_analysis(self, mock_container: Any) -> None:
        args = {
            "target_role": "Data Scientist",
            "current_skills": ["Python"],
        }
        ctx = _make_ctx(args)
        with patch(
            "app.tools.analyze_skill_gap.get_container",
            return_value=mock_container,
        ):
            result = await analyze_skill_gap.on_invoke_tool(ctx, json.dumps(args))
            assert isinstance(result, str)
            assert "Skill Gap Analysis" in result

    @pytest.mark.asyncio
    async def test_identifies_missing_skills(self, mock_container: Any) -> None:
        args = {
            "target_role": "Data Scientist",
            "current_skills": ["Python"],
        }
        ctx = _make_ctx(args)
        with patch(
            "app.tools.analyze_skill_gap.get_container",
            return_value=mock_container,
        ):
            result = await analyze_skill_gap.on_invoke_tool(ctx, json.dumps(args))
            assert "Skills to acquire" in result
            assert "Machine Learning" in result
            assert "Statistics" in result

    @pytest.mark.asyncio
    async def test_identifies_existing_skills(self, mock_container: Any) -> None:
        args = {
            "target_role": "Data Scientist",
            "current_skills": ["Python"],
        }
        ctx = _make_ctx(args)
        with patch(
            "app.tools.analyze_skill_gap.get_container",
            return_value=mock_container,
        ):
            result = await analyze_skill_gap.on_invoke_tool(ctx, json.dumps(args))
            assert "Skills you already have" in result

    @pytest.mark.asyncio
    async def test_no_results_message(self, mock_container: Any) -> None:
        mock_container.vector_store.hybrid_search.return_value = []

        args = {"target_role": "Nonexistent Role XYZ"}
        ctx = _make_ctx(args)
        with patch(
            "app.tools.analyze_skill_gap.get_container",
            return_value=mock_container,
        ):
            result = await analyze_skill_gap.on_invoke_tool(ctx, json.dumps(args))
            assert "No courses found" in result

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_container: Any) -> None:
        mock_container.vector_store.hybrid_search.side_effect = RuntimeError("connection lost")

        args = {"target_role": "Data Scientist"}
        ctx = _make_ctx(args)
        with patch(
            "app.tools.analyze_skill_gap.get_container",
            return_value=mock_container,
        ):
            result = await analyze_skill_gap.on_invoke_tool(ctx, json.dumps(args))
            assert "error" in result.lower() or "try again" in result.lower()
