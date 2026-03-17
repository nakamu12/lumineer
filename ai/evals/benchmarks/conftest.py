"""Shared fixtures for DeepEval benchmarks."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

logger = logging.getLogger(__name__)

DATASETS_DIR = Path(__file__).parent.parent / "datasets"


def load_golden_dataset(filename: str) -> list[dict[str, Any]]:
    """Load a Golden Dataset JSON file."""
    path = DATASETS_DIR / filename
    with open(path, encoding="utf-8") as f:
        data: list[dict[str, Any]] = json.loads(f.read())
    return data


@pytest.fixture(scope="session")
def langfuse_client() -> Any:
    """Return a Langfuse client for the eval session.

    Returns None when LANGFUSE_PUBLIC_KEY is absent (graceful degradation).
    Callers should check ``if langfuse_client is not None`` before using.
    """
    try:
        from app.config.settings import get_settings

        settings = get_settings()
        if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
            logger.info("Langfuse keys absent — skipping eval result logging")
            return None
        from langfuse import Langfuse  # type: ignore[import-not-found]

        client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        logger.info("Langfuse client initialised for eval session")
        return client
    except Exception:
        logger.exception("Langfuse init failed — continuing without it")
        return None


@pytest.fixture(scope="session", autouse=True)
def flush_langfuse(langfuse_client: Any) -> Any:  # type: ignore[return]
    """Flush Langfuse after all benchmarks complete."""
    yield
    if langfuse_client is not None:
        try:
            langfuse_client.flush()
        except Exception:
            logger.exception("Langfuse flush failed")


@pytest.fixture(scope="session")
def search_golden_dataset() -> list[dict[str, Any]]:
    """Load the search agent Golden Dataset."""
    return load_golden_dataset("search_golden.json")


@pytest.fixture(scope="session")
def skill_gap_golden_dataset() -> list[dict[str, Any]]:
    """Load the skill gap agent Golden Dataset."""
    return load_golden_dataset("skill_gap_golden.json")


@pytest.fixture(scope="session")
def path_golden_dataset() -> list[dict[str, Any]]:
    """Load the path agent Golden Dataset."""
    return load_golden_dataset("path_golden.json")
