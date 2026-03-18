"""GetCourseDetailUseCase: retrieve a single course by its Qdrant point ID."""

from __future__ import annotations

from app.domain.entities.course import CourseEntity, CourseFactory
from app.domain.ports.vector_store import VectorStorePort


class CourseNotFoundError(Exception):
    """Raised when a course ID does not exist in the vector store."""

    def __init__(self, course_id: str) -> None:
        super().__init__(f"Course not found: {course_id}")
        self.course_id = course_id


class GetCourseDetailUseCase:
    """Retrieve a single course by its vector store point ID."""

    def __init__(self, vector_store: VectorStorePort) -> None:
        self._vector_store = vector_store

    async def execute(self, course_id: str) -> CourseEntity:
        payload = await self._vector_store.get_by_id(course_id)
        if payload is None:
            raise CourseNotFoundError(course_id)

        return CourseFactory.create(
            id=payload.get("_id", course_id),
            title=payload.get("title", ""),
            description=payload.get("description", ""),
            skills=payload.get("skills") or [],
            level=payload.get("level"),
            organization=payload.get("organization", ""),
            rating=float(payload.get("rating", 0.0)),
            enrolled=int(payload.get("enrolled", 0)),
            num_reviews=payload.get("num_reviews"),
            modules=payload.get("modules"),
            schedule=payload.get("schedule"),
            url=payload.get("url", ""),
            instructor=payload.get("instructor"),
            search_text="",
        )
