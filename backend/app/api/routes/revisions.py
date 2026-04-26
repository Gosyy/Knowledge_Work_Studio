from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.dependencies import (
    get_current_user_id,
    get_deck_revision_service,
    get_presentation_catalog_service,
    get_presentation_plan_snapshot_service,
)
from backend.app.api.schemas import (
    DeckRevisionResponseSchema,
    DeckRevisionSectionRequestSchema,
    DeckRevisionSlideRequestSchema,
    PresentationRestoreRequestSchema,
    PresentationRestoreResponseSchema,
    PresentationRevisionLineageItemSchema,
    PresentationPlanPayloadSchema,
)
from backend.app.services.presentation_catalog_service import PresentationCatalogService
from backend.app.services.slides_service import (
    DeckRestoreRequest,
    DeckRestoreResult,
    DeckRevisionRequest,
    DeckRevisionResult,
    DeckRevisionService,
    PresentationPlan,
    PresentationPlanSnapshotService,
)

router = APIRouter(tags=["presentation revisions"])


@router.post("/presentations/{presentation_id}/revisions/slide", response_model=DeckRevisionResponseSchema)
def revise_presentation_slide(
    presentation_id: str,
    request: DeckRevisionSlideRequestSchema,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    revision_service: DeckRevisionService = Depends(get_deck_revision_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> DeckRevisionResponseSchema:
    # Owner/session authorization check is intentionally done before loading a plan snapshot.
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    try:
        plan = _resolve_revision_plan(
            presentation_id=presentation_id,
            request_plan=request.plan,
            plan_snapshot_service=plan_snapshot_service,
        )
        result = revision_service.regenerate_slide(
            DeckRevisionRequest(
                presentation_id=presentation_id,
                plan=plan,
                instruction=request.instruction,
                template_id=request.template_id,
                task_id=request.task_id,
                owner_user_id=current_user_id,
                target_slide_id=request.target_slide_id,
                target_slide_index=request.target_slide_index,
                change_summary=request.change_summary,
            )
        )
        _persist_revised_plan_snapshot(
            result=result,
            task_id=request.task_id,
            change_summary=request.change_summary,
            plan_snapshot_service=plan_snapshot_service,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _revision_response(result)


@router.post("/presentations/{presentation_id}/revisions/section", response_model=DeckRevisionResponseSchema)
def revise_presentation_section(
    presentation_id: str,
    request: DeckRevisionSectionRequestSchema,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    revision_service: DeckRevisionService = Depends(get_deck_revision_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> DeckRevisionResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    try:
        plan = _resolve_revision_plan(
            presentation_id=presentation_id,
            request_plan=request.plan,
            plan_snapshot_service=plan_snapshot_service,
        )
        result = revision_service.regenerate_section(
            DeckRevisionRequest(
                presentation_id=presentation_id,
                plan=plan,
                instruction=request.instruction,
                template_id=request.template_id,
                task_id=request.task_id,
                owner_user_id=current_user_id,
                target_stage=request.target_stage,
                change_summary=request.change_summary,
            )
        )
        _persist_revised_plan_snapshot(
            result=result,
            task_id=request.task_id,
            change_summary=request.change_summary,
            plan_snapshot_service=plan_snapshot_service,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _revision_response(result)


@router.get("/presentations/{presentation_id}/revisions", response_model=list[PresentationRevisionLineageItemSchema])
def list_presentation_revisions(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    revision_service: DeckRevisionService = Depends(get_deck_revision_service),
) -> list[PresentationRevisionLineageItemSchema]:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    versions = revision_service.list_revision_lineage(presentation_id)
    return [PresentationRevisionLineageItemSchema.model_validate(version) for version in versions]


@router.post(
    "/presentations/{presentation_id}/versions/{version_id}/restore",
    response_model=PresentationRestoreResponseSchema,
)
def restore_presentation_version(
    presentation_id: str,
    version_id: str,
    request: PresentationRestoreRequestSchema,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    revision_service: DeckRevisionService = Depends(get_deck_revision_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> PresentationRestoreResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    if request.confirmation.strip() != "RESTORE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restore confirmation must be exactly RESTORE.",
        )

    target_plan = plan_snapshot_service.get_plan_for_version(version_id)
    if target_plan is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Target presentation version has no editable plan snapshot to restore.",
        )

    try:
        result = revision_service.restore_version(
            DeckRestoreRequest(
                presentation_id=presentation_id,
                target_version_id=version_id,
                owner_user_id=current_user_id,
                task_id=request.task_id,
                change_summary=request.change_summary,
            )
        )
        plan_snapshot_service.create_snapshot(
            presentation_id=presentation_id,
            presentation_version_id=result.version.id,
            plan=target_plan,
            created_from_task_id=request.task_id,
            change_summary=request.change_summary or result.version.change_summary,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _restore_response(result)


def _resolve_revision_plan(
    *,
    presentation_id: str,
    request_plan: PresentationPlanPayloadSchema | None,
    plan_snapshot_service: PresentationPlanSnapshotService,
) -> PresentationPlan:
    if request_plan is not None:
        return request_plan.to_domain()

    plan = plan_snapshot_service.get_latest_plan(presentation_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Presentation has no editable plan snapshot. "
                "Submit an explicit plan or create a plan snapshot before revising."
            ),
        )
    return plan


def _persist_revised_plan_snapshot(
    *,
    result: DeckRevisionResult,
    task_id: str | None,
    change_summary: str | None,
    plan_snapshot_service: PresentationPlanSnapshotService,
) -> None:
    plan_snapshot_service.create_snapshot(
        presentation_id=result.presentation.id,
        presentation_version_id=result.version.id,
        plan=result.revised_plan,
        created_from_task_id=task_id,
        change_summary=change_summary or result.version.change_summary,
    )


def _revision_response(result: DeckRevisionResult) -> DeckRevisionResponseSchema:
    return DeckRevisionResponseSchema(
        presentation_id=result.presentation.id,
        version_id=result.version.id,
        version_number=result.version.version_number,
        parent_version_id=result.version.parent_version_id,
        stored_file_id=result.stored_file.id,
        revised_slide_ids=list(result.revised_slide_ids),
        scope=result.scope.value,
        change_summary=result.version.change_summary,
        created_at=result.version.created_at,
        current_file_id=result.presentation.current_file_id or result.stored_file.id,
        previous_file_id=result.previous_file_id,
    )


def _restore_response(result: DeckRestoreResult) -> PresentationRestoreResponseSchema:
    return PresentationRestoreResponseSchema(
        presentation_id=result.presentation.id,
        restored_version_id=result.version.id,
        restored_version_number=result.version.version_number,
        target_version_id=result.target_version.id,
        target_version_number=result.target_version.version_number,
        parent_version_id=result.version.parent_version_id,
        current_file_id=result.presentation.current_file_id or result.target_version.file_id,
        previous_file_id=result.previous_file_id,
        change_summary=result.version.change_summary,
        created_at=result.version.created_at,
    )
