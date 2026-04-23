from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.routes import get_api_router
from backend.app.core.config import get_settings
from backend.app.integrations.database import initialize_database
from backend.app.observability import RequestLoggingMiddleware, configure_logging


_OPENAPI_TAGS = [
    {"name": "health", "description": "Health and readiness endpoints for backend and deployment checks."},
    {"name": "sessions", "description": "Session lifecycle endpoints used as the frontend container for uploads, tasks, and artifacts."},
    {"name": "uploads", "description": "File upload endpoints that attach source files to a session."},
    {"name": "tasks", "description": "Task creation, synchronous execution, queued execution, semantic execution, and task status endpoints."},
    {"name": "artifacts", "description": "Artifact listing, metadata lookup, and download endpoints for generated outputs."},
]

configure_logging(get_settings().log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database(get_settings())
    yield


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
    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(get_api_router())
    return app


app = create_app()
