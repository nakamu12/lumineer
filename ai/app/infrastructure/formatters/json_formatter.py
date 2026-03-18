"""JsonFormatter: serialize courses as JSON for LLM context."""

import json

from app.domain.entities.course import CourseEntity
from app.infrastructure.formatters.base import BaseFormatter


class JsonFormatter(BaseFormatter):
    """Formats courses as a JSON array string."""

    def format(self, courses: list[CourseEntity]) -> str:
        items = [
            {
                "title": c.title,
                "organization": c.organization,
                "level": c.level,
                "rating": c.rating,
                "enrolled": c.enrolled,
                "skills": c.skills,
                "description": c.description,
                "url": c.url,
                "schedule": c.schedule,
                "instructor": c.instructor,
            }
            for c in courses
        ]
        return json.dumps({"courses": items}, ensure_ascii=False)
