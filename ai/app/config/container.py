"""Dependency injection container."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.domain.ports.embedding import EmbeddingPort
    from app.domain.ports.llm import LLMPort
    from app.domain.ports.vector_store import VectorStorePort


class Container:
    """Simple DI container for managing service dependencies."""

    def __init__(self) -> None:
        self._registry: dict[type[Any], Any] = {}

    def register(self, port: type[Any], implementation: Any) -> None:
        """Register an implementation for a given port."""
        self._registry[port] = implementation

    def resolve(self, port: type[Any]) -> Any:
        """Resolve an implementation for a given port."""
        if port not in self._registry:
            raise KeyError(f"No implementation registered for {port.__name__}")
        return self._registry[port]

    @property
    def vector_store(self) -> VectorStorePort:
        """Return the registered VectorStorePort implementation."""
        from app.domain.ports.vector_store import VectorStorePort

        return self.resolve(VectorStorePort)  # type: ignore[return-value]

    @property
    def embedding(self) -> EmbeddingPort:
        """Return the registered EmbeddingPort implementation."""
        from app.domain.ports.embedding import EmbeddingPort

        return self.resolve(EmbeddingPort)  # type: ignore[return-value]

    @property
    def llm(self) -> LLMPort:
        """Return the registered LLMPort implementation."""
        from app.domain.ports.llm import LLMPort

        return self.resolve(LLMPort)  # type: ignore[return-value]


_container: Container | None = None


def get_container() -> Container:
    """Return the global DI container."""
    global _container
    if _container is None:
        _container = Container()
    return _container
