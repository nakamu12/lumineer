"""Dependency injection container."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.domain.ports.embedding import EmbeddingPort
    from app.domain.ports.llm import LLMPort
    from app.domain.ports.vector_store import VectorStorePort
    from app.observability.langfuse_tracer import LangfuseTracer
    from app.observability.metrics import MetricsCollector
    from app.observability.token_tracker import TokenTracker


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

        result: VectorStorePort = self.resolve(VectorStorePort)
        return result

    @property
    def embedding(self) -> EmbeddingPort:
        """Return the registered EmbeddingPort implementation."""
        from app.domain.ports.embedding import EmbeddingPort

        result: EmbeddingPort = self.resolve(EmbeddingPort)
        return result

    @property
    def llm(self) -> LLMPort:
        """Return the registered LLMPort implementation."""
        from app.domain.ports.llm import LLMPort

        result: LLMPort = self.resolve(LLMPort)
        return result

    @property
    def metrics(self) -> MetricsCollector:
        """Return the registered MetricsCollector."""
        from app.observability.metrics import MetricsCollector

        result: MetricsCollector = self.resolve(MetricsCollector)
        return result

    @property
    def tracer(self) -> LangfuseTracer:
        """Return the registered LangfuseTracer."""
        from app.observability.langfuse_tracer import LangfuseTracer

        result: LangfuseTracer = self.resolve(LangfuseTracer)
        return result

    @property
    def token_tracker(self) -> TokenTracker:
        """Return the registered TokenTracker."""
        from app.observability.token_tracker import TokenTracker

        result: TokenTracker = self.resolve(TokenTracker)
        return result


_container: Container | None = None


def get_container() -> Container:
    """Return the global DI container."""
    global _container
    if _container is None:
        _container = Container()
    return _container


def build_container() -> Container:
    """Wire up all ports with their concrete implementations."""
    from app.config.settings import get_settings
    from app.domain.ports.embedding import EmbeddingPort
    from app.domain.ports.vector_store import VectorStorePort
    from app.infrastructure.embeddings.openai_embedding_adapter import OpenAIEmbeddingAdapter
    from app.infrastructure.vectordb.qdrant_search_adapter import QdrantSearchAdapter
    from app.observability.langfuse_tracer import LangfuseTracer, create_langfuse_tracer
    from app.observability.metrics import MetricsCollector, create_metrics_collector
    from app.observability.token_tracker import TokenTracker

    settings = get_settings()
    container = get_container()

    container.register(
        EmbeddingPort,
        OpenAIEmbeddingAdapter(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        ),
    )
    container.register(
        VectorStorePort,
        QdrantSearchAdapter(
            url=settings.QDRANT_URL,
            collection_name=settings.QDRANT_COLLECTION,
            api_key=settings.QDRANT_API_KEY,
        ),
    )

    # Observability
    metrics = create_metrics_collector()
    tracer = create_langfuse_tracer(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
    )
    token_tracker = TokenTracker(metrics=metrics, tracer=tracer)

    container.register(MetricsCollector, metrics)
    container.register(LangfuseTracer, tracer)
    container.register(TokenTracker, token_tracker)

    return container
