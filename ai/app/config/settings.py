"""Application settings managed by Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.local",
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
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "courses"

    # Ingestion
    DATA_PATH: str = "../data/coursera.parquet"
    PREPROCESSED_PATH: str = "data/processed/preprocessed.jsonl"
    BATCH_SIZE_LLM: int = 10
    BATCH_SIZE_EMBEDDING: int = 100
    BATCH_SIZE_UPSERT: int = 200
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 120

    # RAG defaults
    RERANKER_STRATEGY: Literal["none", "heuristic", "cross-encoder"] = "none"
    CONTEXT_FORMAT: Literal["json", "toon"] = "json"

    @model_validator(mode="after")
    def validate_prod(self) -> "Settings":
        if self.APP_ENV == "prod" and not self.QDRANT_API_KEY:
            raise ValueError("QDRANT_API_KEY is required in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
