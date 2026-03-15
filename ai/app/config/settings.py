"""Application settings managed via Pydantic Settings."""
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    APP_ENV: Literal["dev", "prod"] = "dev"
    OPENAI_API_KEY: str = ""
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_API_KEY: str | None = None
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    RERANKER_STRATEGY: Literal["none", "heuristic", "cross-encoder"] = "none"
    CONTEXT_FORMAT: Literal["json", "toon"] = "json"
    TOP_K: int = 10
    SIMILARITY_THRESHOLD: float = 0.7
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    @model_validator(mode="after")
    def validate_prod(self) -> "Settings":
        """Enforce production-only required fields."""
        if self.APP_ENV == "prod" and not self.QDRANT_API_KEY:
            raise ValueError("QDRANT_API_KEY is required in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
