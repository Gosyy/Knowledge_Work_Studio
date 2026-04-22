from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from backend.app.core.config import get_settings
from backend.app.integrations.database import initialize_database
from backend.app.api.routes import get_api_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)

_OPENAPI_TAGS = [
    {"name": "health", "description": "Health and readiness endpoints for backend and deployment checks."},
    {"name": "sessions", "description": "Session lifecycle endpoints used as the frontend container for uploads, tasks, and artifacts."},
    {"name": "uploads", "description": "File upload endpoints that attach source files to a session."},
    {"name": "tasks", "description": "Task creation, synchronous execution, queued execution, semantic execution, and task status endpoints."},
    {"name": "artifacts", "description": "Artifact listing, metadata lookup, and download endpoints for generated outputs."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting KW Studio backend")
    initialize_database(get_settings())
    yield
    logger.info("Stopping KW Studio backend")


def create_app() -> FastAPI:
    app = FastAPI(
        title="KW Studio API",
        version="0.1.0",
        description=(
            "Stable frontend-facing MVP contract for sessions, uploads, tasks, semantic tasks, "
            "artifacts, health, and readiness in the offline intranet deployment profile."
        ),
        openapi_tags=_OPENAPI_TAGS,
        lifespan=lifespan,
    )
    app.include_router(get_api_router())
    return app


app = create_app()
