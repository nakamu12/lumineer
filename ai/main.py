"""AI Processing Service entrypoint."""
import uvicorn

from app.config.settings import get_settings
from app.interfaces.api.routes import create_app

app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_ENV == "dev",
    )
