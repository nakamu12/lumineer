"""Unit tests for csv_loader module."""

import pytest

from app.infrastructure.ingestion.csv_loader import (
    _parse_enrolled,
    _parse_rating,
    _parse_skills,
)


class TestParseSkills:
    def test_empty_list_string(self) -> None:
        assert _parse_skills("[]") == []

    def test_valid_skills(self) -> None:
        result = _parse_skills("['Python', 'Machine Learning']")
        assert result == ["Python", "Machine Learning"]

    def test_none_value(self) -> None:
        assert _parse_skills("None") == []

    def test_nan_value(self) -> None:
        assert _parse_skills("nan") == []

    def test_strips_whitespace(self) -> None:
        result = _parse_skills("['  Python ', ' ML  ']")
        assert result == ["Python", "ML"]


class TestParseEnrolled:
    def test_comma_separated(self) -> None:
        assert _parse_enrolled("5,710") == 5710

    def test_large_number(self) -> None:
        assert _parse_enrolled("170,608") == 170608

    def test_integer(self) -> None:
        assert _parse_enrolled(1000) == 1000

    def test_float(self) -> None:
        assert _parse_enrolled(1500.0) == 1500

    def test_zero(self) -> None:
        assert _parse_enrolled("0") == 0


class TestParseRating:
    def test_string_float(self) -> None:
        assert _parse_rating("4.6") == pytest.approx(4.6)

    def test_float(self) -> None:
        assert _parse_rating(4.9) == pytest.approx(4.9)

    def test_invalid(self) -> None:
        assert _parse_rating("n/a") == 0.0
