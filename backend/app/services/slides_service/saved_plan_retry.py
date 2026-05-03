from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Literal
from uuid import uuid4

from backend.app.domain import Artifact, PresentationPlanSnapshot
from backend.app.services.slides_service.approved_plan import (
    ApprovedPlanRenderRequest,
    ApprovedPlanRenderResult,
    render_approved_plan_to_pptx,
)
from backend.app.services.slides_service.approved_plan_lifecycle import (
    ArtifactRegistrationService,
    SlidesTaskEvent,
)
from backend.app.services.slides_service.outline import PresentationPlan
from backend.app.services.slides_service.plan_snapshot import (
    PresentationPlanSnapshotService,
    deserialize_presentation_plan,
)
from backend.app.services.slides_service.task_event_contract import (
    REDACTED_PAYLOAD_KEYS,
    SAFE_PAYLOAD_FIELDS,
    SLIDES_RETRY_EVENT_SEQUENCE,
    SLIDES_TASK_EVENT_TYPES,
    SLIDES_TASK_WORKFLOW_ID,
)

RenderMode = Literal["adaptive", "template"]


@dataclass(frozen=True)
class SavedPlanRetryRequest:
    saved_plan_snapshot_id: str
    session_id: str
    retry_task_id: str
    parent_task_id: str
    presentation_id: str
    operator_instruction: str
    render_mode: RenderMode = "adaptive"
    template_id: str = "business_clean"
    new_plan_snapshot_id: str | None = None
    new_presentation_version_id: str | None = None
    artifact_filename: str = "retry-from-saved-plan.pptx"
    operator_user_id: str = "user_local_default"


@dataclass(frozen=True)
class SavedPlanRetryResult:
    render_result: ApprovedPlanRenderResult
    saved_plan_snapshot: PresentationPlanSnapshot
    new_plan_snapshot: PresentationPlanSnapshot
    artifact: Artifact
    events: tuple[SlidesTaskEvent, ...]
    safe_metadata: dict[str, object]

    @property
    def event_types(self) -> tuple[str, ...]:
        return tuple(event.event_type for event in self.events)

    def as_report(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact.id,
            "artifact_filename": self.artifact.filename,
            "parent_plan_snapshot_id": self.saved_plan_snapshot.id,
            "new_plan_snapshot_id": self.new_plan_snapshot.id,
            "event_types": list(self.event_types),
            "safe_metadata": dict(self.safe_metadata),
        }


def retry_saved_plan_with_lifecycle(
    request: SavedPlanRetryRequest,
    *,
    plan_snapshot_service: PresentationPlanSnapshotService,
    artifact_service: ArtifactRegistrationService,
) -> SavedPlanRetryResult:
    """Regenerate a deck from a saved plan snapshot and emit retry lifecycle events.

    RF2.4 intentionally does not add a public endpoint, migration, queue,
    provenance artifact, visual QA runtime, or Kimi-level quality claim.
    """

    _validate_request(request)

    saved_snapshot = plan_snapshot_service.snapshots.get(request.saved_plan_snapshot_id)
    if saved_snapshot is None:
        raise ValueError(f"Saved plan snapshot '{request.saved_plan_snapshot_id}' not found.")
    if saved_snapshot.presentation_id != request.presentation_id:
        raise ValueError(
            "Saved plan snapshot presentation_id does not match retry presentation_id."
        )

    plan = deserialize_presentation_plan(saved_snapshot.snapshot_json)
    _validate_saved_plan(plan)

    new_snapshot_id = request.new_plan_snapshot_id or f"plansnap_retry_{uuid4().hex}"
    instruction_digest = _instruction_digest(request.operator_instruction)
    change_summary = f"Retry from saved plan; instruction_digest={instruction_digest}"

    render_result = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=plan,
            plan_snapshot_id=new_snapshot_id,
            approval_status="approved",
            render_mode=request.render_mode,
            template_id=request.template_id,
            session_id=request.session_id,
            task_id=request.retry_task_id,
            presentation_id=request.presentation_id,
            artifact_filename=request.artifact_filename,
            operator_user_id=request.operator_user_id,
        )
    )

    artifact = artifact_service.create_artifact_from_bytes(
        session_id=request.session_id,
        task_id=request.retry_task_id,
        filename=render_result.artifact_filename,
        content_type=render_result.content_type,
        content=render_result.artifact_content,
    )

    new_snapshot = plan_snapshot_service.create_snapshot(
        presentation_id=request.presentation_id,
        presentation_version_id=request.new_presentation_version_id,
        plan=plan,
        created_from_task_id=request.retry_task_id,
        change_summary=change_summary,
        snapshot_id=new_snapshot_id,
    )

    pre_generation_payload = {
        "plan_snapshot_id": saved_snapshot.id,
        "presentation_id": request.presentation_id,
        "presentation_version_id": saved_snapshot.presentation_version_id,
        "render_mode": request.render_mode,
        "retry_of_task_id": request.parent_task_id,
        "change_summary": "Retry requested from saved plan.",
    }
    new_artifact_payload = {
        "plan_snapshot_id": new_snapshot.id,
        "presentation_id": request.presentation_id,
        "presentation_version_id": new_snapshot.presentation_version_id,
        "render_mode": request.render_mode,
        "artifact_id": artifact.id,
        "artifact_filename": artifact.filename,
        "retry_of_task_id": request.parent_task_id,
        "change_summary": "Retry generated from saved plan.",
    }

    events = (
        _event(request, "slides.retry.from_saved_plan.requested", pre_generation_payload),
        _event(request, "slides.retry.saved_plan_snapshot.loaded", pre_generation_payload),
        _event(request, "slides.retry.plan.validated", pre_generation_payload),
        _event(request, "slides.retry.render_mode.confirmed", pre_generation_payload),
        _event(request, "slides.retry.generation.started", pre_generation_payload),
        _event(request, "artifact.registered", new_artifact_payload),
        _event(request, "plan.snapshot.registered", new_artifact_payload),
        _event(request, "slides.retry.generation.completed", new_artifact_payload),
    )
    _validate_retry_event_sequence(events)

    safe_metadata = {
        "workflow_id": "slides.saved_plan_retry",
        "schema_version": "slides_saved_plan_retry.v1",
        "session_id": request.session_id,
        "retry_task_id": request.retry_task_id,
        "parent_task_id": request.parent_task_id,
        "presentation_id": request.presentation_id,
        "parent_plan_snapshot_id": saved_snapshot.id,
        "parent_presentation_version_id": saved_snapshot.presentation_version_id,
        "new_plan_snapshot_id": new_snapshot.id,
        "new_presentation_version_id": new_snapshot.presentation_version_id,
        "new_artifact_id": artifact.id,
        "artifact_filename": artifact.filename,
        "render_mode": request.render_mode,
        "template_id": request.template_id,
        "retry_instruction_digest": instruction_digest,
        "raw_operator_instruction_stored": False,
        "event_count": len(events),
        "event_types": tuple(event.event_type for event in events),
        "saved_plan_snapshot_loaded": True,
        "new_plan_snapshot_persisted": True,
        "new_artifact_registered": True,
        "retry_parent_links_present": True,
        "append_only_event_stream": True,
        "network_required": False,
        "runtime_changed_by_rf2_4": True,
        "dependency_versions_changed_by_rf2_4": False,
        "dockerfiles_changed_by_rf2_4": False,
        "kimi_grade_supported": False,
        "whole_project_kimi_level_supported": False,
    }

    return SavedPlanRetryResult(
        render_result=render_result,
        saved_plan_snapshot=saved_snapshot,
        new_plan_snapshot=new_snapshot,
        artifact=artifact,
        events=events,
        safe_metadata=safe_metadata,
    )


def _validate_request(request: SavedPlanRetryRequest) -> None:
    if not request.saved_plan_snapshot_id.strip():
        raise ValueError("Saved-plan retry requires saved_plan_snapshot_id.")
    if not request.session_id.strip():
        raise ValueError("Saved-plan retry requires a non-empty session_id.")
    if not request.retry_task_id.strip():
        raise ValueError("Saved-plan retry requires a non-empty retry_task_id.")
    if not request.parent_task_id.strip():
        raise ValueError("Saved-plan retry requires parent_task_id.")
    if request.retry_task_id == request.parent_task_id:
        raise ValueError("Saved-plan retry requires retry_task_id to differ from parent_task_id.")
    if not request.presentation_id.strip():
        raise ValueError("Saved-plan retry requires a non-empty presentation_id.")
    if not request.operator_instruction.strip():
        raise ValueError("Saved-plan retry requires explicit operator_instruction.")
    if request.render_mode not in ("adaptive", "template"):
        raise ValueError("Saved-plan retry render_mode must be 'adaptive' or 'template'.")
    if request.render_mode == "template" and not request.template_id.strip():
        raise ValueError("Saved-plan retry template mode requires template_id.")
    if not request.artifact_filename.strip():
        raise ValueError("Saved-plan retry requires artifact_filename.")


def _validate_saved_plan(plan: PresentationPlan) -> None:
    if not plan.slides:
        raise ValueError("Saved-plan retry requires a snapshot with at least one slide.")
    if plan.target_slide_count != len(plan.slides):
        raise ValueError("Saved-plan retry requires target_slide_count to match slide count.")


def _event(
    request: SavedPlanRetryRequest,
    event_type: str,
    payload: dict[str, object],
) -> SlidesTaskEvent:
    if event_type not in SLIDES_TASK_EVENT_TYPES:
        raise ValueError(f"Unsupported slides retry event type: {event_type}")
    return SlidesTaskEvent(
        event_id=f"evt_{uuid4().hex}",
        task_id=request.retry_task_id,
        session_id=request.session_id,
        workflow_id=SLIDES_TASK_WORKFLOW_ID,
        event_type=event_type,
        created_at=_utc_now(),
        safe_payload=_safe_payload(payload),
    )


def _safe_payload(payload: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    allowed = set(SAFE_PAYLOAD_FIELDS)
    redacted = {key.lower() for key in REDACTED_PAYLOAD_KEYS}

    for key, value in payload.items():
        normalized = key.lower()
        if normalized in redacted:
            raise ValueError(f"Forbidden sensitive payload key: {key}")
        if key not in allowed:
            continue
        if value is None:
            continue
        safe[key] = value
    return safe


def _validate_retry_event_sequence(events: tuple[SlidesTaskEvent, ...]) -> None:
    actual = tuple(event.event_type for event in events)
    if actual != SLIDES_RETRY_EVENT_SEQUENCE:
        raise ValueError(f"RF2.4 retry event order mismatch: {actual!r}")


def _instruction_digest(operator_instruction: str) -> str:
    return "sha256:" + sha256(operator_instruction.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
