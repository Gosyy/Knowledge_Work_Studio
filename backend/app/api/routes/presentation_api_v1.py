from __future__ import annotations

from typing import Any, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.dependencies import (
    get_current_user_id,
    get_presentation_catalog_service,
    get_presentation_plan_snapshot_service,
)
from backend.app.api.schemas import (
    PresentationApiContractStatusSchema,
    PresentationApiCreateRequestSchema,
    PresentationApiMetadataResponseSchema,
    PresentationApiPlanRequestSchema,
    PresentationApiPlanSnapshotResponseSchema,
    PresentationApiRenderRequestSchema,
    PresentationApiSlidePatchRequestSchema,
    PresentationApiSlidesResponseSchema,
    PresentationApiSourceAttachRequestSchema,
    PresentationSchema,
)
from backend.app.domain import PresentationPlanSnapshot
from backend.app.services import PresentationCatalogService
from backend.app.services.slides_service import PresentationPlanSnapshotService
from backend.app.api.routes.presentations import _sanitize_public_plan_payload

router = APIRouter(prefix="/api/v1", tags=["presentation-api-v1"])

_API_VERSION = "presentation_api.v1"
_UNIMPLEMENTED_DETAIL = (
    "KR-7C API-first Presentation contract endpoint is declared but its runtime implementation belongs to a later KR-7C subphase."
)


def _not_implemented() -> NoReturn:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_UNIMPLEMENTED_DETAIL)


@router.post(
    "/presentations",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first presentation creation contract.",
)
def create_presentation_v1(_request: PresentationApiCreateRequestSchema) -> PresentationApiContractStatusSchema:
    _not_implemented()


@router.get(
    "/presentations/{presentation_id}",
    response_model=PresentationApiMetadataResponseSchema,
    summary="Read presentation metadata through the API-first presentation contract.",
)
def get_presentation_v1(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: PresentationCatalogService = Depends(get_presentation_catalog_service),
) -> PresentationApiMetadataResponseSchema:
    presentation = service.get_presentation_for_user(
        presentation_id=presentation_id,
        owner_user_id=current_user_id,
    )
    return PresentationApiMetadataResponseSchema(
        api_version=_API_VERSION,
        presentation=PresentationSchema(**presentation.__dict__),
    )


@router.post(
    "/presentations/{presentation_id}/sources",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first source attachment contract.",
)
def attach_presentation_source_v1(
    presentation_id: str,
    _request: PresentationApiSourceAttachRequestSchema,
) -> PresentationApiContractStatusSchema:
    _not_implemented()


@router.get(
    "/presentations/{presentation_id}/plan",
    response_model=PresentationApiPlanSnapshotResponseSchema,
    summary="Read the latest public-safe presentation plan snapshot through the API-first contract.",
)
def get_presentation_plan_v1(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> PresentationApiPlanSnapshotResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    snapshot = plan_snapshot_service.get_latest_snapshot(presentation_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation '{presentation_id}' has no API-first plan snapshot yet.",
        )
    return _api_plan_snapshot_response(snapshot)


@router.post(
    "/presentations/{presentation_id}/plan",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first PresentationIR planning contract.",
)
def plan_presentation_v1(
    presentation_id: str,
    _request: PresentationApiPlanRequestSchema,
) -> PresentationApiContractStatusSchema:
    _not_implemented()


@router.get(
    "/presentations/{presentation_id}/slides",
    response_model=PresentationApiSlidesResponseSchema,
    summary="Read public-safe slide payloads from the latest plan snapshot.",
)
def list_presentation_slides_v1(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> PresentationApiSlidesResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    snapshot = plan_snapshot_service.get_latest_snapshot(presentation_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation '{presentation_id}' has no API-first slide plan snapshot yet.",
        )

    plan = _sanitize_public_plan_payload(snapshot.snapshot_json)
    if not isinstance(plan, dict):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Presentation plan snapshot is not a JSON object.")
    slides = plan.get("slides", [])
    if not isinstance(slides, list):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Presentation plan snapshot slides field is invalid.")

    schema_version = str(plan.get("schema_version") or "legacy_plan_snapshot")
    return PresentationApiSlidesResponseSchema(
        api_version=_API_VERSION,
        presentation_id=presentation_id,
        snapshot_id=snapshot.id,
        presentation_version_id=snapshot.presentation_version_id,
        schema_version=schema_version,
        slides=[item for item in slides if isinstance(item, dict)],
    )


@router.patch(
    "/presentations/{presentation_id}/slides/{slide_id}",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first slide patch contract.",
)
def patch_presentation_slide_v1(
    presentation_id: str,
    slide_id: str,
    _request: PresentationApiSlidePatchRequestSchema,
) -> PresentationApiContractStatusSchema:
    _not_implemented()


@router.post(
    "/presentations/{presentation_id}/render",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first render contract.",
)
def render_presentation_v1(
    presentation_id: str,
    _request: PresentationApiRenderRequestSchema | None = None,
) -> PresentationApiContractStatusSchema:
    _not_implemented()


@router.post(
    "/presentations/{presentation_id}/export",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first export contract.",
)
def export_presentation_v1(
    presentation_id: str,
    _request: PresentationApiRenderRequestSchema | None = None,
) -> PresentationApiContractStatusSchema:
    _not_implemented()


@router.get(
    "/presentations/{presentation_id}/quality",
    response_model=PresentationApiContractStatusSchema,
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Declare the API-first quality report contract.",
)
def get_presentation_quality_v1(presentation_id: str) -> PresentationApiContractStatusSchema:
    _not_implemented()


def _api_plan_snapshot_response(snapshot: PresentationPlanSnapshot) -> PresentationApiPlanSnapshotResponseSchema:
    plan = _sanitize_public_plan_payload(snapshot.snapshot_json)
    if not isinstance(plan, dict):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Presentation plan snapshot is not a JSON object.")
    schema_version = str(plan.get("schema_version") or "legacy_plan_snapshot")
    return PresentationApiPlanSnapshotResponseSchema(
        api_version=_API_VERSION,
        snapshot_id=snapshot.id,
        presentation_id=snapshot.presentation_id,
        presentation_version_id=snapshot.presentation_version_id,
        created_from_task_id=snapshot.created_from_task_id,
        change_summary=snapshot.change_summary,
        created_at=snapshot.created_at,
        schema_version=schema_version,
        plan=plan,
    )
