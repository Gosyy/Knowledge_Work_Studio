from fastapi import APIRouter

from backend.app.api.routes.health import router as health_router


def get_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)
    return router
