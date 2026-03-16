"""Unit tests for Formatter strategies."""

import json

import pytest

from app.domain.entities.course import CourseFactory
from app.infrastructure.formatters import JsonFormatter, ToonFormatter, create_formatter


def _make_course(**kwargs):  # type: ignore[no-untyped-def]
    defaults = dict(
        title="Python for Everybody",
        description="Learn Python programming",
        skills=["Python", "Data Structures"],
        level="Beginner",
        organization="University of Michigan",
        rating=4.8,
        enrolled=1_000_000,
        num_reviews=50000,
        modules=None,
        schedule="4 weeks",
        url="https://coursera.org/python",
        instructor="Chuck",
        search_text="python beginner",
    )
    defaults.update(kwargs)
    return CourseFactory.create(**defaults)


class TestJsonFormatter:
    def test_format_single_course(self) -> None:
        course = _make_course()
        result = JsonFormatter().format([course])
        data = json.loads(result)
        assert "courses" in data
        assert len(data["courses"]) == 1
        c = data["courses"][0]
        assert c["title"] == "Python for Everybody"
        assert c["organization"] == "University of Michigan"
        assert c["level"] == "Beginner"
        assert c["rating"] == 4.8
        assert "Python" in c["skills"]

    def test_format_empty(self) -> None:
        result = JsonFormatter().format([])
        data = json.loads(result)
        assert data["courses"] == []

    def test_format_multiple_courses(self) -> None:
        courses = [_make_course(title=f"Course {i}") for i in range(3)]
        result = JsonFormatter().format(courses)
        data = json.loads(result)
        assert len(data["courses"]) == 3


class TestToonFormatter:
    def test_format_single_course(self) -> None:
        course = _make_course()
        result = ToonFormatter().format([course])
        assert result.startswith("courses[1]{")
        assert "title,org,level,rating,enrolled,skills" in result
        assert "Python for Everybody" in result
        assert "University of Michigan" in result
        assert "Beginner" in result

    def test_format_empty(self) -> None:
        result = ToonFormatter().format([])
        assert "courses[0]" in result
        assert "no results" in result

    def test_skills_with_comma_are_quoted(self) -> None:
        course = _make_course(skills=["Python", "Data Structures"])
        result = ToonFormatter().format([course])
        assert '"Python, Data Structures"' in result

    def test_title_with_comma_is_quoted(self) -> None:
        course = _make_course(title="R, Python, and Statistics")
        result = ToonFormatter().format([course])
        assert '"R, Python, and Statistics"' in result

    def test_format_multiple_courses(self) -> None:
        courses = [_make_course(title=f"Course {i}") for i in range(5)]
        result = ToonFormatter().format(courses)
        assert result.startswith("courses[5]{")
        lines = result.strip().split("\n")
        assert len(lines) == 6  # header + 5 data rows


class TestCreateFormatter:
    def test_json(self) -> None:
        assert isinstance(create_formatter("json"), JsonFormatter)

    def test_toon(self) -> None:
        assert isinstance(create_formatter("toon"), ToonFormatter)

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown formatter"):
            create_formatter("xml")
