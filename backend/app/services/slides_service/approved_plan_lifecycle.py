from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from backend.app.domain import Artifact, PresentationPlanSnapshot
from backend.app.services.slides_service.approved_plan import (
    ApprovedPlanRenderRequest,
    ApprovedPlanRenderResult,
    render_approved_plan_to_pptx,
)
from backend.app.services.slides_service.outline import PresentationPlan
from backend.app.services.slides_service.plan_snapshot import PresentationPlanSnapshotService
from backend.app.services.slides_service.task_event_contract import (
    REDACTED_PAYLOAD_KEYS,
    SAFE_PAYLOAD_FIELDS,
    SLIDES_TASK_EVENT_TYPES,
    SLIDES_TASK_WORKFLOW_ID,
)


class ArtifactRegistrationService(Protocol):
    def create_artifact_from_bytes(
        self,
        *,
        session_id: str,
        task_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Artifact: ...


RF2_3_EVENT_SEQUENCE: tuple[str, ...] = (
    "slides.plan.approved",
    "slides.render_mode.selected",
    "slides.generation.started",
    "artifact.registered",
    "plan.snapshot.registered",
    "slides.generation.completed",
)


@dataclass(frozen=True)
class SlidesTaskEvent:
    event_id: str
    task_id: str
    session_id: str
    workflow_id: str
    event_type: str
    created_at: str
    safe_payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "workflow_id": self.workflow_id,
            "event_type": self.event_type,
            "created_at": self.created_at,
            "safe_payload": dict(self.safe_payload),
        }


@dataclass(frozen=True)
class ApprovedPlanLifecycleRequest:
    plan: PresentationPlan
    session_id: str
    task_id: str
    presentation_id: str
    approval_status: str = "approved"
    render_mode: str = "adaptive"
    template_id: str = "business_clean"
    presentation_version_id: str | None = None
    plan_snapshot_id: str | None = None
    change_summary: str = "Approved plan rendered to deterministic PPTX."
    artifact_filename: str = "approved-plan-deck.pptx"
    operator_user_id: str = "user_local_default"


@dataclass(frozen=True)
class ApprovedPlanLifecycleResult:
    render_result: ApprovedPlanRenderResult
    plan_snapshot: PresentationPlanSnapshot
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
            "plan_snapshot_id": self.plan_snapshot.id,
            "presentation_id": self.plan_snapshot.presentation_id,
            "presentation_version_id": self.plan_snapshot.presentation_version_id,
            "event_types": list(self.event_types),
            "safe_metadata": dict(self.safe_metadata),
        }


def render_approved_plan_with_lifecycle(
    request: ApprovedPlanLifecycleRequest,
    *,
    plan_snapshot_service: PresentationPlanSnapshotService,
    artifact_service: ArtifactRegistrationService,
) -> ApprovedPlanLifecycleResult:
    """Render an approved plan and wire it into snapshot/artifact/event lifecycle.

    RF2.3 intentionally does not add a public endpoint, migration, retry runtime,
    provenance artifact, or Kimi-level quality claims.
    """

    _validate_request(request)
    snapshot_id = request.plan_snapshot_id or f"plansnap_{uuid4().hex}"

    render_result = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=request.plan,
            plan_snapshot_id=snapshot_id,
            approval_status=request.approval_status,
            render_mode=request.render_mode,  # type: ignore[arg-type]
            template_id=request.template_id,
            session_id=request.session_id,
            task_id=request.task_id,
            presentation_id=request.presentation_id,
            artifact_filename=request.artifact_filename,
            operator_user_id=request.operator_user_id,
        )
    )

    artifact = artifact_service.create_artifact_from_bytes(
        session_id=request.session_id,
        task_id=request.task_id,
        filename=render_result.artifact_filename,
        content_type=render_result.content_type,
        content=render_result.artifact_content,
    )

    plan_snapshot = plan_snapshot_service.create_snapshot(
        presentation_id=request.presentation_id,
        presentation_version_id=request.presentation_version_id,
        plan=request.plan,
        created_from_task_id=request.task_id,
        change_summary=request.change_summary,
        snapshot_id=snapshot_id,
    )

    base_payload = {
        "plan_snapshot_id": plan_snapshot.id,
        "presentation_id": request.presentation_id,
        "presentation_version_id": request.presentation_version_id,
        "render_mode": request.render_mode,
        "change_summary": request.change_summary,
    }
    artifact_payload = {
        **base_payload,
        "artifact_id": artifact.id,
        "artifact_filename": artifact.filename,
    }

    events = (
        _event(request, "slides.plan.approved", base_payload),
        _event(request, "slides.render_mode.selected", base_payload),
        _event(request, "slides.generation.started", base_payload),
        _event(request, "artifact.registered", artifact_payload),
        _event(request, "plan.snapshot.registered", artifact_payload),
        _event(request, "slides.generation.completed", artifact_payload),
    )
    _validate_event_sequence(events)

    safe_metadata = {
        "workflow_id": "slides.approved_plan_lifecycle",
        "schema_version": "slides_approved_plan_lifecycle.v1",
        "session_id": request.session_id,
        "task_id": request.task_id,
        "presentation_id": request.presentation_id,
        "presentation_version_id": request.presentation_version_id,
        "plan_snapshot_id": plan_snapshot.id,
        "artifact_id": artifact.id,
        "artifact_filename": artifact.filename,
        "render_mode": request.render_mode,
        "template_id": request.template_id,
        "event_count": len(events),
        "event_types": tuple(event.event_type for event in events),
        "append_only_event_stream": True,
        "plan_snapshot_persisted": True,
        "artifact_registered": True,
        "network_required": False,
        "runtime_changed_by_rf2_3": True,
        "dependency_versions_changed_by_rf2_3": False,
        "dockerfiles_changed_by_rf2_3": False,
        "kimi_grade_supported": False,
        "whole_project_kimi_level_supported": False,
    }

    return ApprovedPlanLifecycleResult(
        render_result=render_result,
        plan_snapshot=plan_snapshot,
        artifact=artifact,
        events=events,
        safe_metadata=safe_metadata,
    )


def _validate_request(request: ApprovedPlanLifecycleRequest) -> None:
    if request.approval_status != "approved":
        raise ValueError("Approved-plan lifecycle requires approval_status='approved'.")
    if not request.session_id.strip():
        raise ValueError("Approved-plan lifecycle requires a non-empty session_id.")
    if not request.task_id.strip():
        raise ValueError("Approved-plan lifecycle requires a non-empty task_id.")
    if not request.presentation_id.strip():
        raise ValueError("Approved-plan lifecycle requires a non-empty presentation_id.")
    if not request.change_summary.strip():
        raise ValueError("Approved-plan lifecycle requires a non-empty change_summary.")


def _event(
    request: ApprovedPlanLifecycleRequest,
    event_type: str,
    payload: dict[str, object],
) -> SlidesTaskEvent:
    if event_type not in SLIDES_TASK_EVENT_TYPES:
        raise ValueError(f"Unsupported slides task event type: {event_type}")
    return SlidesTaskEvent(
        event_id=f"evt_{uuid4().hex}",
        task_id=request.task_id,
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


def _validate_event_sequence(events: tuple[SlidesTaskEvent, ...]) -> None:
    actual = tuple(event.event_type for event in events)
    if actual != RF2_3_EVENT_SEQUENCE:
        raise ValueError(f"RF2.3 event order mismatch: {actual!r}")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
