"""Base interface for context formatters."""

from abc import ABC, abstractmethod

from app.domain.entities.course import CourseEntity


class BaseFormatter(ABC):
    """Strategy interface for formatting search results as LLM context."""

    @abstractmethod
    def format(self, courses: list[CourseEntity]) -> str:
        """Format a list of courses into a string for LLM context."""
        ...
