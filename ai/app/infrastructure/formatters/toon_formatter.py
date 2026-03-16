"""ToonFormatter: Token-Oriented Object Notation — ~50% fewer tokens than JSON.

Format example:
    courses[3]{title,org,level,rating,enrolled,skills}:
      ML Specialization,Stanford,Beginner,4.8,12345,"Python, TensorFlow"
      ...
"""

from app.domain.entities.course import CourseEntity
from app.infrastructure.formatters.base import BaseFormatter

_FIELDS = ("title", "org", "level", "rating", "enrolled", "skills")


def _escape(value: str) -> str:
    """Wrap in quotes if the value contains a comma."""
    return f'"{value}"' if "," in value else value


class ToonFormatter(BaseFormatter):
    """TOON format: one header row, one CSV-like data row per course."""

    def format(self, courses: list[CourseEntity]) -> str:
        if not courses:
            return "courses[0]{}: (no results)"

        header = f"courses[{len(courses)}]{{{','.join(_FIELDS)}}}:"
        rows = []
        for c in courses:
            skills_str = _escape(", ".join(c.skills) if c.skills else "")
            row = ",".join(
                [
                    _escape(c.title),
                    _escape(c.organization),
                    c.level or "None",
                    str(round(c.rating, 1)),
                    str(c.enrolled),
                    skills_str,
                ]
            )
            rows.append(f"  {row}")

        return "\n".join([header] + rows)
