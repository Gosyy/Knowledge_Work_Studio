from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.dependencies import (
    get_current_user_id,
    get_deck_revision_service,
    get_presentation_catalog_service,
    get_presentation_plan_snapshot_service,
)
from backend.app.api.schemas import (
    PresentationPlanDiffSchema,
    PresentationPlanSlideDeltaSchema,
    PresentationPlanSnapshotSchema,
    PresentationSchema,
    PresentationVersionSummarySchema,
)
from backend.app.domain import PresentationPlanSnapshot
from backend.app.services import PresentationCatalogService
from backend.app.services.slides_service import (
    DeckRevisionService,
    PresentationPlan,
    PresentationPlanSnapshotService,
    deserialize_presentation_plan,
)

router = APIRouter(tags=["presentations"])

_UNSAFE_PLAN_KEYS = {"storage_key", "storage_uri"}
_UNSAFE_STRING_PREFIXES = ("local://", "file://")


@router.get("/sessions/{session_id}/presentations", response_model=list[PresentationSchema])
def list_session_presentations(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: PresentationCatalogService = Depends(get_presentation_catalog_service),
) -> list[PresentationSchema]:
    presentations = service.list_session_presentations_for_user(
        session_id=session_id,
        owner_user_id=current_user_id,
    )
    return [PresentationSchema(**presentation.__dict__) for presentation in presentations]


@router.get("/presentations/{presentation_id}", response_model=PresentationSchema)
def get_presentation(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: PresentationCatalogService = Depends(get_presentation_catalog_service),
) -> PresentationSchema:
    presentation = service.get_presentation_for_user(
        presentation_id=presentation_id,
        owner_user_id=current_user_id,
    )
    return PresentationSchema(**presentation.__dict__)


@router.get(
    "/presentations/{presentation_id}/versions",
    response_model=list[PresentationVersionSummarySchema],
)
def list_presentation_versions(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: PresentationCatalogService = Depends(get_presentation_catalog_service),
) -> list[PresentationVersionSummarySchema]:
    versions = service.list_presentation_versions_for_user(
        presentation_id=presentation_id,
        owner_user_id=current_user_id,
    )
    return [PresentationVersionSummarySchema(**version.__dict__) for version in versions]


@router.get("/presentations/{presentation_id}/plan", response_model=PresentationPlanSnapshotSchema)
def get_current_presentation_plan(
    presentation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> PresentationPlanSnapshotSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    snapshot = plan_snapshot_service.get_latest_snapshot(presentation_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation '{presentation_id}' has no editable plan snapshot.",
        )
    return _snapshot_response(snapshot)


@router.get(
    "/presentations/{presentation_id}/versions/{version_id}/plan",
    response_model=PresentationPlanSnapshotSchema,
)
def get_presentation_version_plan(
    presentation_id: str,
    version_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> PresentationPlanSnapshotSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)
    snapshot = plan_snapshot_service.get_snapshot_for_version(version_id)
    if snapshot is None or snapshot.presentation_id != presentation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation plan snapshot for version '{version_id}' was not found.",
        )
    return _snapshot_response(snapshot)


@router.get(
    "/presentations/{presentation_id}/revisions/{version_id}/diff",
    response_model=PresentationPlanDiffSchema,
)
def get_presentation_revision_plan_diff(
    presentation_id: str,
    version_id: str,
    current_user_id: str = Depends(get_current_user_id),
    catalog_service: PresentationCatalogService = Depends(get_presentation_catalog_service),
    revision_service: DeckRevisionService = Depends(get_deck_revision_service),
    plan_snapshot_service: PresentationPlanSnapshotService = Depends(get_presentation_plan_snapshot_service),
) -> PresentationPlanDiffSchema:
    catalog_service.get_presentation_for_user(presentation_id=presentation_id, owner_user_id=current_user_id)

    versions = {version.id: version for version in revision_service.list_revision_lineage(presentation_id)}
    version = versions.get(version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation version '{version_id}' was not found.",
        )
    if version.parent_version_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presentation version '{version_id}' has no parent version to diff against.",
        )

    compared_snapshot = plan_snapshot_service.get_snapshot_for_version(version_id)
    base_snapshot = plan_snapshot_service.get_snapshot_for_version(version.parent_version_id)
    if (
        compared_snapshot is None
        or base_snapshot is None
        or compared_snapshot.presentation_id != presentation_id
        or base_snapshot.presentation_id != presentation_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparable presentation plan snapshots were not found for this revision.",
        )

    base_plan = deserialize_presentation_plan(base_snapshot.snapshot_json)
    compared_plan = deserialize_presentation_plan(compared_snapshot.snapshot_json)
    deltas = _diff_plans(base_plan=base_plan, compared_plan=compared_plan)

    return PresentationPlanDiffSchema(
        presentation_id=presentation_id,
        base_version_id=version.parent_version_id,
        compared_version_id=version_id,
        base_snapshot_id=base_snapshot.id,
        compared_snapshot_id=compared_snapshot.id,
        changed_slide_count=len(deltas),
        slide_deltas=deltas,
    )


def _snapshot_response(snapshot: PresentationPlanSnapshot) -> PresentationPlanSnapshotSchema:
    return PresentationPlanSnapshotSchema(
        snapshot_id=snapshot.id,
        presentation_id=snapshot.presentation_id,
        presentation_version_id=snapshot.presentation_version_id,
        created_from_task_id=snapshot.created_from_task_id,
        change_summary=snapshot.change_summary,
        created_at=snapshot.created_at,
        plan=_sanitize_public_plan_payload(snapshot.snapshot_json),
    )


def _sanitize_public_plan_payload(value: Any) -> Any:
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, child in value.items():
            if key in _UNSAFE_PLAN_KEYS:
                continue
            safe[key] = _sanitize_public_plan_payload(child)
        return safe
    if isinstance(value, list):
        return [_sanitize_public_plan_payload(item) for item in value]
    if isinstance(value, str) and value.startswith(_UNSAFE_STRING_PREFIXES):
        return None
    return deepcopy(value)


def _diff_plans(*, base_plan: PresentationPlan, compared_plan: PresentationPlan) -> list[PresentationPlanSlideDeltaSchema]:
    base_by_id = {slide.slide_id: (index, slide) for index, slide in enumerate(base_plan.slides)}
    compared_by_id = {slide.slide_id: (index, slide) for index, slide in enumerate(compared_plan.slides)}
    slide_ids = [slide.slide_id for slide in base_plan.slides]
    slide_ids.extend(slide.slide_id for slide in compared_plan.slides if slide.slide_id not in base_by_id)

    deltas: list[PresentationPlanSlideDeltaSchema] = []
    for slide_id in slide_ids:
        base_entry = base_by_id.get(slide_id)
        compared_entry = compared_by_id.get(slide_id)

        if base_entry is None and compared_entry is not None:
            after_index, after_slide = compared_entry
            deltas.append(
                PresentationPlanSlideDeltaSchema(
                    slide_id=slide_id,
                    change_type="added",
                    before_index=None,
                    after_index=after_index,
                    title_before=None,
                    title_after=after_slide.title,
                    story_arc_stage_before=None,
                    story_arc_stage_after=after_slide.story_arc_stage.value,
                    layout_hint_before=None,
                    layout_hint_after=after_slide.layout_hint,
                    bullets_added=list(after_slide.bullets),
                    bullets_removed=[],
                    speaker_notes_changed=after_slide.speaker_notes is not None,
                )
            )
            continue

        if base_entry is not None and compared_entry is None:
            before_index, before_slide = base_entry
            deltas.append(
                PresentationPlanSlideDeltaSchema(
                    slide_id=slide_id,
                    change_type="removed",
                    before_index=before_index,
                    after_index=None,
                    title_before=before_slide.title,
                    title_after=None,
                    story_arc_stage_before=before_slide.story_arc_stage.value,
                    story_arc_stage_after=None,
                    layout_hint_before=before_slide.layout_hint,
                    layout_hint_after=None,
                    bullets_added=[],
                    bullets_removed=list(before_slide.bullets),
                    speaker_notes_changed=before_slide.speaker_notes is not None,
                )
            )
            continue

        if base_entry is None or compared_entry is None:
            continue

        before_index, before_slide = base_entry
        after_index, after_slide = compared_entry
        bullets_added = [bullet for bullet in after_slide.bullets if bullet not in before_slide.bullets]
        bullets_removed = [bullet for bullet in before_slide.bullets if bullet not in after_slide.bullets]
        speaker_notes_changed = before_slide.speaker_notes != after_slide.speaker_notes
        changed = (
            before_index != after_index
            or before_slide.title != after_slide.title
            or before_slide.story_arc_stage != after_slide.story_arc_stage
            or before_slide.layout_hint != after_slide.layout_hint
            or bool(bullets_added)
            or bool(bullets_removed)
            or speaker_notes_changed
        )
        if not changed:
            continue
        deltas.append(
            PresentationPlanSlideDeltaSchema(
                slide_id=slide_id,
                change_type="modified",
                before_index=before_index,
                after_index=after_index,
                title_before=before_slide.title,
                title_after=after_slide.title,
                story_arc_stage_before=before_slide.story_arc_stage.value,
                story_arc_stage_after=after_slide.story_arc_stage.value,
                layout_hint_before=before_slide.layout_hint,
                layout_hint_after=after_slide.layout_hint,
                bullets_added=bullets_added,
                bullets_removed=bullets_removed,
                speaker_notes_changed=speaker_notes_changed,
            )
        )

    return deltas
