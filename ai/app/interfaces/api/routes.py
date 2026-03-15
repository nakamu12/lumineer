"""Litestar API route definitions."""
from litestar import Litestar, get
from litestar.config.cors import CORSConfig

from app.config.settings import get_settings


@get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "ok",
        "service": "lumineer-ai",
        "env": settings.APP_ENV,
    }


def create_app() -> Litestar:
    """Create and configure the Litestar application."""
    cors_config = CORSConfig(allow_origins=["*"])

    return Litestar(
        route_handlers=[health_check],
        cors_config=cors_config,
    )
