"""Loader for Coursera parquet/CSV data."""

import ast
import re
from pathlib import Path
from typing import Any

import pandas as pd


def _parse_skills(raw: str) -> list[str]:
    """Parse skills from string representation of list."""
    if not raw or raw in ("[]", "nan", "None"):
        return []
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, list):
            return [str(s).strip() for s in parsed if s]
    except (ValueError, SyntaxError):
        pass
    return []


def _parse_enrolled(raw: str | float | int) -> int:
    """Parse enrolled count from string like '5,710' or '1.2M'."""
    if isinstance(raw, (int, float)):
        return max(0, int(raw))
    raw = str(raw).strip()
    # Remove commas: '170,608' -> '170608'
    raw = raw.replace(",", "")
    # Handle K/M suffix
    raw = re.sub(r"[^0-9.]", "", raw)
    try:
        return max(0, int(float(raw)))
    except ValueError:
        return 0


def _parse_rating(raw: str | float) -> float:
    """Parse rating to float."""
    try:
        return float(str(raw).strip())
    except ValueError:
        return 0.0


def load_courses(data_path: str | Path) -> list[dict[str, Any]]:
    """Load Coursera parquet/CSV and return list of raw course dicts."""
    path = Path(data_path)
    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)

    courses = []
    for _, row in df.iterrows():
        description = str(row.get("Description", "") or "").strip()
        if not description or description == "nan":
            description = ""

        instructor_str = str(row.get("Instructor", "") or "").strip()
        instructor: str | None = instructor_str if instructor_str and instructor_str != "nan" \
            else None

        modules_str = str(row.get("Modules/Courses", "") or "").strip()
        modules: str | None = modules_str if modules_str and modules_str != "nan" else None

        schedule_str = str(row.get("Schedule", "") or "").strip()
        schedule: str | None = schedule_str if schedule_str and schedule_str != "nan" else None

        num_reviews_raw = row.get("num_reviews")
        num_reviews = None
        if num_reviews_raw is not None and str(num_reviews_raw) not in ("nan", "None", ""):
            try:
                num_reviews = int(float(str(num_reviews_raw)))
            except (ValueError, TypeError):
                num_reviews = None

        courses.append(
            {
                "title": str(row.get("title", "")).strip(),
                "description": description,
                "skills": _parse_skills(str(row.get("Skills", "[]"))),
                "level": str(row.get("Level", "") or "").strip() or None,
                "organization": str(row.get("Organization", "")).strip(),
                "rating": _parse_rating(row.get("rating", "0")),
                "enrolled": _parse_enrolled(row.get("enrolled", 0)),
                "num_reviews": num_reviews,
                "modules": modules,
                "schedule": schedule,
                "url": str(row.get("URL", "")).strip(),
                "instructor": instructor,
            }
        )

    return courses
