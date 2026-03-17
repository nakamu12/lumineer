"""Shared fixtures for DeepEval benchmarks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

DATASETS_DIR = Path(__file__).parent.parent / "datasets"


def load_golden_dataset(filename: str) -> list[dict[str, Any]]:
    """Load a Golden Dataset JSON file."""
    path = DATASETS_DIR / filename
    with open(path, encoding="utf-8") as f:
        data: list[dict[str, Any]] = json.loads(f.read())
    return data


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
