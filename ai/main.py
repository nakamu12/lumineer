"""AI Processing Service entrypoint.

Serves two ASGI apps on the same port:
  /      → Litestar REST API (health, metrics, search, agents/chat)
  /mcp   → FastMCP server (Streamable HTTP transport, OAuth 2.1 auth)
"""

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount

from app.config.settings import get_settings
from app.interfaces.api.routes import create_app
from app.interfaces.mcp.server import create_mcp_asgi_app

_litestar_app = create_app()
_mcp_app = create_mcp_asgi_app()

# Route /mcp/* to the MCP server; everything else to Litestar.
app = Starlette(
    routes=[
        Mount("/mcp", app=_mcp_app),
        Mount("/", app=_litestar_app),  # type: ignore[arg-type]
    ]
)

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_ENV == "dev",
    )
