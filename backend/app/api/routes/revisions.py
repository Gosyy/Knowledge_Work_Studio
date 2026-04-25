from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.dependencies import (
    get_current_user_id,
    get_deck_revision_service,
    get_presentation_catalog_service,
)
from backend.app.api.schemas import (
    DeckRevisionResponseSchema,
    DeckRevisionSectionRequestSchema,
    DeckRevisionSlideRequestSchema,
    PresentationRevisionLineageItemSchema,
)
from backend.app.services.presentation_catalog_service import PresentationCatalogService
from backend.app.services.slides_service import DeckRevisionRequest, DeckRevisionResult, DeckRevisionService

router = APIRouter(tags=["presentation revisions"])


@router.post("/presentations/{presentation_id}/revisions/slide", response_model=DeckRevisionResponseSchema)
def revise_presentation_slide(
    presentation_id: str,
    request: DeckRevisionSlideRequestSchema,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    revision_service: DeckRevisionService = Depends(get_deck_revision_service),
) -> DeckRevisionResponseSchema:
    # Owner/session authorization check is intentionally done before revision.
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    try:
        result = revision_service.regenerate_slide(
            DeckRevisionRequest(
                presentation_id=presentation_id,
                plan=request.plan.to_domain(),
                instruction=request.instruction,
                template_id=request.template_id,
                task_id=request.task_id,
                owner_user_id=current_user_id,
                target_slide_id=request.target_slide_id,
                target_slide_index=request.target_slide_index,
                change_summary=request.change_summary,
            )
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
) -> DeckRevisionResponseSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    try:
        result = revision_service.regenerate_section(
            DeckRevisionRequest(
                presentation_id=presentation_id,
                plan=request.plan.to_domain(),
                instruction=request.instruction,
                template_id=request.template_id,
                task_id=request.task_id,
                owner_user_id=current_user_id,
                target_stage=request.target_stage,
                change_summary=request.change_summary,
            )
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
