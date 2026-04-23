import logging
from typing import Any

from fastapi import APIRouter, Response, status

from backend.app.core.config import get_settings
from backend.app.deployment import build_deployment_readiness

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health() -> dict[str, str]:
    logger.info("health_checked")
    return {"status": "ok"}


@router.get("/ready")
async def readiness(response: Response) -> dict[str, Any]:
    readiness_result = build_deployment_readiness(get_settings())
    if readiness_result.status != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    logger.info(
        "readiness_evaluated",
        extra={
            "readiness_status": readiness_result.status,
            "readiness_error_count": len(readiness_result.errors),
            "readiness_warning_count": len(readiness_result.warnings),
        },
    )
    return readiness_result.as_dict()
