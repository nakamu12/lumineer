"""Port definition for LLM operations."""
from abc import ABC, abstractmethod
from typing import Any


class LLMPort(ABC):
    """Abstract interface for language model operations."""

    @abstractmethod
    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Generate a completion for the given prompt."""
        ...
