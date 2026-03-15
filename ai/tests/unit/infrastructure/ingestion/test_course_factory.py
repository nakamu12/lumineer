"""Unit tests for CourseFactory."""

from app.domain.entities.course import CourseFactory


def _make_course(**overrides):
    defaults = dict(
        title="Python for Data Science",
        description="Learn Python for data analysis.",
        skills=["Python", "Pandas"],
        level="Beginner level",
        organization="Coursera",
        rating=4.8,
        enrolled=12000,
        num_reviews=300,
        modules="4 modules",
        schedule="10 hours",
        url="https://coursera.org/course/python-ds",
        instructor="John Doe",
        search_text="Python for Data Science. Python, Pandas",
    )
    defaults.update(overrides)
    return CourseFactory.create(**defaults)


class TestCourseFactory:
    def test_normalizes_level_beginner(self) -> None:
        course = _make_course(level="Beginner level")
        assert course.level == "Beginner"

    def test_normalizes_level_intermediate(self) -> None:
        course = _make_course(level="Intermediate level")
        assert course.level == "Intermediate"

    def test_normalizes_level_advanced(self) -> None:
        course = _make_course(level="Advanced level")
        assert course.level == "Advanced"

    def test_none_level(self) -> None:
        course = _make_course(level=None)
        assert course.level is None

    def test_unknown_level_becomes_none(self) -> None:
        course = _make_course(level="Mixed level")
        assert course.level is None

    def test_generates_id_if_not_provided(self) -> None:
        course = _make_course()
        assert course.id is not None
        assert len(course.id) == 36  # UUID format

    def test_uses_provided_id(self) -> None:
        course = _make_course(id="fixed-id-123")
        assert course.id == "fixed-id-123"

    def test_strips_whitespace_from_title(self) -> None:
        course = _make_course(title="  My Course  ")
        assert course.title == "My Course"

    def test_rating_clamped(self) -> None:
        course = _make_course(rating=6.0)
        assert course.rating == 5.0

    def test_enrolled_non_negative(self) -> None:
        course = _make_course(enrolled=-100)
        assert course.enrolled == 0

    def test_skills_filters_empty_strings(self) -> None:
        course = _make_course(skills=["Python", "", "  ", "ML"])
        assert course.skills == ["Python", "ML"]
