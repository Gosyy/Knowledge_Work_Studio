from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Literal

from backend.app.services.slides_service.generator import generate_pptx_from_plan
from backend.app.services.slides_service.outline import PresentationPlan, SlideOutlineItem, plan_to_outline


RenderMode = Literal["adaptive", "template"]

PPTX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
ALLOWED_RENDER_MODES: tuple[str, ...] = ("adaptive", "template")
SAFE_APPROVED_PLAN_RENDER_EVENTS: tuple[str, ...] = (
    "slides.approved_plan.render.requested",
    "slides.approved_plan.validated",
    "slides.approved_plan.render.started",
    "slides.approved_plan.render.completed",
)


@dataclass(frozen=True)
class ApprovedPlanRenderRequest:
    plan: PresentationPlan
    plan_snapshot_id: str
    approval_status: str = "approved"
    render_mode: RenderMode = "adaptive"
    template_id: str = "business_clean"
    session_id: str | None = None
    task_id: str | None = None
    presentation_id: str | None = None
    artifact_filename: str = "approved-plan-deck.pptx"
    operator_user_id: str = "user_local_default"


@dataclass(frozen=True)
class ApprovedPlanRenderResult:
    artifact_content: bytes
    content_type: str
    artifact_filename: str
    checksum_sha256: str
    size_bytes: int
    slide_count: int
    plan_snapshot_id: str
    render_mode: str
    template_id: str
    outline: tuple[SlideOutlineItem, ...]
    safe_metadata: dict[str, object]
    safe_event_types: tuple[str, ...]


def render_approved_plan_to_pptx(request: ApprovedPlanRenderRequest) -> ApprovedPlanRenderResult:
    """Render an already-approved PresentationPlan into deterministic PPTX bytes.

    This is intentionally narrow: no LLM call, no internet, no persistence,
    no artifact registry write, and no provenance manifest emission.
    """

    _validate_request(request)

    artifact_content = generate_pptx_from_plan(request.plan, template_id=request.template_id)
    digest = sha256(artifact_content).hexdigest()
    slide_count = len(request.plan.slides)
    outline = plan_to_outline(request.plan)
    metadata = {
        "workflow_id": "slides.approved_plan_runtime",
        "schema_version": "slides_approved_plan_render.v1",
        "plan_snapshot_id": request.plan_snapshot_id,
        "presentation_id": request.presentation_id,
        "session_id": request.session_id,
        "task_id": request.task_id,
        "render_mode": request.render_mode,
        "template_id": request.template_id,
        "slide_count": slide_count,
        "artifact_filename": request.artifact_filename,
        "content_type": PPTX_CONTENT_TYPE,
        "checksum_sha256": digest,
        "size_bytes": len(artifact_content),
        "approval_status": request.approval_status,
        "operator_user_id": request.operator_user_id,
        "network_required": False,
        "kimi_grade_supported": False,
        "whole_project_kimi_level_supported": False,
    }

    return ApprovedPlanRenderResult(
        artifact_content=artifact_content,
        content_type=PPTX_CONTENT_TYPE,
        artifact_filename=request.artifact_filename,
        checksum_sha256=digest,
        size_bytes=len(artifact_content),
        slide_count=slide_count,
        plan_snapshot_id=request.plan_snapshot_id,
        render_mode=request.render_mode,
        template_id=request.template_id,
        outline=outline,
        safe_metadata=metadata,
        safe_event_types=SAFE_APPROVED_PLAN_RENDER_EVENTS,
    )


def _validate_request(request: ApprovedPlanRenderRequest) -> None:
    if request.approval_status != "approved":
        raise ValueError("Approved-plan rendering requires approval_status='approved'.")

    if not request.plan_snapshot_id.strip():
        raise ValueError("Approved-plan rendering requires a non-empty plan_snapshot_id.")

    if request.render_mode not in ALLOWED_RENDER_MODES:
        raise ValueError(f"Unsupported render mode: {request.render_mode!r}.")

    if request.render_mode == "template" and not request.template_id.strip():
        raise ValueError("Template render mode requires an explicit local template_id.")

    if not request.template_id.strip():
        raise ValueError("Approved-plan rendering requires a local template_id.")

    if not request.plan.slides:
        raise ValueError("Approved-plan rendering requires at least one planned slide.")

    if request.plan.target_slide_count != len(request.plan.slides):
        raise ValueError("Approved-plan target_slide_count must match the concrete slides length.")

    if not request.artifact_filename.endswith(".pptx"):
        raise ValueError("Approved-plan artifact_filename must end with .pptx.")

    if ".." in request.artifact_filename or "/" in request.artifact_filename or "\\" in request.artifact_filename:
        raise ValueError("Approved-plan artifact_filename must be a safe local filename.")
