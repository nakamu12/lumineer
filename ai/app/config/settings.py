"""Application settings managed by Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env.local from project root (two levels up from ai/app/config/)
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env.local"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: Literal["dev", "prod"] = "dev"

    # OpenAI
    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSIONS: int = 3072
    LLM_MODEL: str = "gpt-4o-mini"

    # Qdrant
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "courses"

    # Ingestion
    DATA_PATH: str = "../data/coursera.parquet"
    PREPROCESSED_PATH: str = "data/processed/preprocessed.jsonl"
    BATCH_SIZE_LLM: int = 10
    BATCH_SIZE_EMBEDDING: int = 100
    BATCH_SIZE_UPSERT: int = 50
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 120

    # RAG defaults
    RERANKER_STRATEGY: Literal["none", "heuristic", "cross-encoder"] = "none"
    CONTEXT_FORMAT: Literal["json", "toon"] = "json"
    TOP_K: int = 10
    SIMILARITY_THRESHOLD: float = 0.7

    # Agent settings
    AGENT_MODEL: str = "gpt-4o-mini"
    AGENT_MAX_TURNS: int = 10

    # Rate Limiting (L5)
    RATE_LIMIT_MAX_REQUESTS: int = 30
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Token Budget (L5)
    MAX_INPUT_TOKENS: int = 10_000
    MAX_OUTPUT_TOKENS: int = 4_000
    MAX_TOTAL_TOKENS: int = 14_000
    MAX_CORRECTIVE_RAG_RETRIES: int = 3

    # Langfuse (optional — disabled when keys are absent)
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str = "http://localhost:3003"

    # MCP Server (stretch goal — OAuth 2.1 + Keycloak)
    # Set KEYCLOAK_URL to enable auth (e.g., "http://keycloak:8080")
    # Leave unset in dev to run without authentication
    KEYCLOAK_URL: str | None = None
    KEYCLOAK_REALM: str = "lumineer"
    MCP_REQUIRE_AUTH: bool = False  # Set to True in prod to enforce token validation
    # Public URL of the MCP resource server (used in OAuth 2.1 metadata).
    # Defaults to http://{HOST}:{PORT}/mcp; override in prod with HTTPS URL.
    MCP_RESOURCE_SERVER_URL: str | None = None

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    @model_validator(mode="after")
    def validate_prod(self) -> "Settings":
        """Enforce production-only required fields."""
        # QDRANT_API_KEY is no longer required — GCE Qdrant uses firewall-only protection
        if self.APP_ENV == "prod":
            if self.MCP_REQUIRE_AUTH and not self.MCP_RESOURCE_SERVER_URL:
                raise ValueError(
                    "MCP_RESOURCE_SERVER_URL is required when MCP_REQUIRE_AUTH=true in production"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()  # type: ignore[call-arg]
