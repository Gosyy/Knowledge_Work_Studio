from fastapi import APIRouter

from backend.app.api.routes.artifacts import router as artifacts_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.sessions import router as sessions_router
from backend.app.api.routes.tasks import router as tasks_router
from backend.app.api.routes.uploads import router as uploads_router


def get_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)
    router.include_router(sessions_router)
    router.include_router(uploads_router)
    router.include_router(tasks_router)
    router.include_router(artifacts_router)
    return router
