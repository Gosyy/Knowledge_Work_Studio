from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PresentationPlanSnapshotSchema(BaseModel):
    snapshot_id: str
    presentation_id: str
    presentation_version_id: str | None
    created_from_task_id: str | None
    change_summary: str | None
    created_at: datetime
    plan: dict[str, Any]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "snapshot_id": "plansnap_123",
                "presentation_id": "pres_123",
                "presentation_version_id": "presver_123",
                "created_from_task_id": "task_123",
                "change_summary": "Initial editable plan",
                "created_at": "2026-04-25T12:00:00Z",
                "plan": {
                    "schema_version": 1,
                    "deck_title": "Quarterly Review",
                    "slides": [{"slide_id": "slide_001", "title": "Quarterly Review"}],
                },
            }
        }
    )


class PresentationPlanSlideDeltaSchema(BaseModel):
    slide_id: str
    change_type: str = Field(pattern="^(added|removed|modified)$")
    before_index: int | None
    after_index: int | None
    title_before: str | None
    title_after: str | None
    story_arc_stage_before: str | None
    story_arc_stage_after: str | None
    layout_hint_before: str | None
    layout_hint_after: str | None
    bullets_added: list[str] = Field(default_factory=list)
    bullets_removed: list[str] = Field(default_factory=list)
    speaker_notes_changed: bool = False


class PresentationPlanDiffSchema(BaseModel):
    presentation_id: str
    base_version_id: str
    compared_version_id: str
    base_snapshot_id: str
    compared_snapshot_id: str
    changed_slide_count: int
    slide_deltas: list[PresentationPlanSlideDeltaSchema]
