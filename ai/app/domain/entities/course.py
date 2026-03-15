"""Course entity and factory."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class CourseEntity:
    id: str
    title: str
    description: str
    skills: list[str]
    level: str | None  # Beginner / Intermediate / Advanced / None
    organization: str
    rating: float
    enrolled: int
    num_reviews: int | None
    modules: str | None
    schedule: str | None
    url: str
    instructor: str | None
    search_text: str  # LLM-generated text used for embedding


class CourseFactory:
    """Creates and validates CourseEntity instances."""

    VALID_LEVELS = {"Beginner", "Intermediate", "Advanced"}

    @classmethod
    def create(
        cls,
        *,
        title: str,
        description: str,
        skills: list[str],
        level: str | None,
        organization: str,
        rating: float,
        enrolled: int,
        num_reviews: int | None,
        modules: str | None,
        schedule: str | None,
        url: str,
        instructor: str | None,
        search_text: str,
        id: str | None = None,
    ) -> CourseEntity:
        normalized_level = cls._normalize_level(level)
        return CourseEntity(
            id=id or str(uuid.uuid4()),
            title=title.strip(),
            description=description.strip() if description else "",
            skills=[s.strip() for s in skills if s.strip()],
            level=normalized_level,
            organization=organization.strip(),
            rating=max(0.0, min(5.0, rating)),
            enrolled=max(0, enrolled),
            num_reviews=max(0, num_reviews) if num_reviews is not None else None,
            modules=modules.strip() if modules else None,
            schedule=schedule.strip() if schedule else None,
            url=url.strip(),
            instructor=instructor.strip() if instructor else None,
            search_text=search_text.strip(),
        )

    @classmethod
    def _normalize_level(cls, raw: str | None) -> str | None:
        if not raw:
            return None
        # Handle values like "Beginner level", "Intermediate level"
        for level in cls.VALID_LEVELS:
            if level.lower() in raw.lower():
                return level
        return None
