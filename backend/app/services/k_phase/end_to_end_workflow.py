from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any

from backend.app.services.k_phase.local_gigachat_planner import (
    K1LLMProvider,
    K1PlanningRequest,
    K1PlanningResult,
    LocalGigaChatPlanningEngine,
)
from backend.app.services.k_phase.plan_editor import K2EvidenceLink, K2PlanEditorResult, K2PlanEditorWorkflow
from backend.app.services.k_phase.renderer_quality import RendererQualityResult, build_default_k3_quality_profile, improve_presentation_plan_render_quality
from backend.app.services.k_phase.source_to_slide_provenance import (
    K5SourceToSlideProvenanceResult,
    attach_k5_provenance_to_manifest,
    build_source_to_slide_provenance,
    validate_k5_source_to_slide_result,
)
from backend.app.services.k_phase.visual_qa import (
    VisualQAOperatorReview,
    VisualQAReviewRequest,
    VisualQARuntimeRequest,
    VisualQARuntimeResult,
    build_visual_qa_operator_review,
    run_visual_qa_runtime,
)
from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, ApprovedPlanRenderResult, render_approved_plan_to_pptx

K6_CHECKPOINT = "K6"
K6_SCHEMA_VERSION = "k6.end_to_end_kimi_like_workflow.v1"
K6_WORKFLOW_ID = "k_phase.end_to_end_kimi_like_workflow"
K_PHASE_BRANCH = "8_K_Phase"
K6_BASE_AFTER_K5 = "fafdfd0840428f2d006da19c3c56eec64701168c"
K6_EVENT_TYPES: tuple[str, ...] = (
    "k6.workflow.started",
    "k6.k1.plan.completed",
    "k6.k2.plan.approved",
    "k6.k3.renderer_quality.completed",
    "k6.k5.source_to_slide_provenance.completed",
    "k6.render.completed",
    "k6.k4.visual_qa.completed",
    "k6.operator_gate.completed",
)
_FORBIDDEN_SAFE_TEXT = ("password", "secret", "token", "api_key", "client_secret", "authorization")


@dataclass(frozen=True)
class K6EndToEndWorkflowRequest:
    source_text: str
    source_refs: tuple[dict[str, Any], ...] = ()
    audience: str = "executive_operator"
    deck_goal: str = "Create a source-grounded executive presentation with visible quality gates."
    target_slide_count: int = 7
    render_mode: str = "adaptive"
    template_id: str = "business_clean"
    operator_user_id: str = "user_local_default"
    session_id: str | None = None
    task_id: str | None = None
    presentation_id: str | None = None
    artifact_filename: str = "k6-end-to-end-workflow.pptx"
    allow_deterministic_fallback: bool = True
    operator_visual_qa_decision: str = "approve"


@dataclass(frozen=True)
class K6WorkflowArtifact:
    artifact_kind: str
    filename: str
    content_type: str
    checksum_sha256: str
    size_bytes: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class K6WorkflowGate:
    gate_id: str
    status: str
    details: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {"gate_id": self.gate_id, "status": self.status, "details": dict(self.details)}


@dataclass(frozen=True)
class K6EndToEndWorkflowResult:
    planning_result: K1PlanningResult
    plan_editor_result: K2PlanEditorResult
    renderer_quality_result: RendererQualityResult
    provenance_result: K5SourceToSlideProvenanceResult
    render_result: ApprovedPlanRenderResult
    visual_qa_result: VisualQARuntimeResult
    operator_review: VisualQAOperatorReview
    workflow_artifacts: tuple[K6WorkflowArtifact, ...]
    gates: tuple[K6WorkflowGate, ...]
    manifest: dict[str, object]
    safe_metadata: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.safe_metadata.get("status"),
            "safe_metadata": dict(self.safe_metadata),
            "gates": [gate.as_dict() for gate in self.gates],
            "workflow_artifacts": [artifact.as_dict() for artifact in self.workflow_artifacts],
            "visual_qa_status": self.visual_qa_result.status,
            "operator_review_status": self.operator_review.review_status,
            "slide_count": self.safe_metadata.get("slide_count"),
        }


def run_k6_end_to_end_workflow(
    request: K6EndToEndWorkflowRequest,
    *,
    llm_provider: K1LLMProvider | None = None,
) -> K6EndToEndWorkflowResult:
    """Run the controlled K6 local end-to-end presentation workflow.

    K6 composes the already accepted K-phase layers into one deterministic,
    operator-gated workflow. It remains offline/intranet-safe by default and
    does not add a public endpoint, DB migration, dependency change, Docker
    change, cloud LLM, cloud vision, or a whole-product Kimi-level claim.
    """

    _validate_request(request)
    events = list(K6_EVENT_TYPES)

    planner = LocalGigaChatPlanningEngine(llm_provider=llm_provider, production_mode=True)
    planning = planner.plan(
        K1PlanningRequest(
            source_text=request.source_text,
            audience=request.audience,
            deck_goal=request.deck_goal,
            target_slide_count=request.target_slide_count,
            source_refs=tuple(_string_source_ref(ref) for ref in request.source_refs),
            allow_deterministic_fallback=request.allow_deterministic_fallback,
            operator_user_id=request.operator_user_id,
            session_id=request.session_id,
            task_id=request.task_id,
        )
    )

    editor = K2PlanEditorWorkflow()
    evidence_links = _k2_evidence_links_by_slide(planning.plan, request.source_refs)
    session_result = editor.create_session(
        planning.plan,
        operator_user_id=request.operator_user_id,
        render_mode=request.render_mode,
        template_id=request.template_id if request.render_mode == "template" else None,
        source_links_by_slide_id=evidence_links,
        retry_of_task_id=request.task_id,
    )
    approval_requested = editor.request_approval(session_result.session, operator_user_id=request.operator_user_id)
    approved = editor.approve(approval_requested.session, operator_user_id=request.operator_user_id)
    if approved.approved_plan is None:
        raise RuntimeError("K6 K2 approval did not produce an approved PresentationPlan")

    quality_profile = build_default_k3_quality_profile(render_mode=request.render_mode, template_id=request.template_id)
    quality = improve_presentation_plan_render_quality(approved.approved_plan, profile=quality_profile)

    provenance = build_source_to_slide_provenance(
        quality.render_plan,
        source_text=request.source_text,
        source_refs=request.source_refs,
    )
    provenance_errors = validate_k5_source_to_slide_result(provenance)
    if provenance_errors:
        raise RuntimeError("K6 K5 provenance validation failed: " + "; ".join(provenance_errors))

    render = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=provenance.plan,
            plan_snapshot_id=_stable_id("k6_plan_snapshot", planning.prompt_digest, provenance.manifest_section["integrity"]["section_digest"]),
            approval_status="approved",
            render_mode=request.render_mode,
            template_id=request.template_id,
            session_id=request.session_id,
            task_id=request.task_id,
            presentation_id=request.presentation_id,
            artifact_filename=request.artifact_filename,
            operator_user_id=request.operator_user_id,
        )
    )

    visual_qa = run_visual_qa_runtime(
        VisualQARuntimeRequest(
            plan=provenance.plan,
            artifact_content=render.artifact_content,
            plan_snapshot_id=render.plan_snapshot_id,
            render_mode=render.render_mode,
            template_id=render.template_id,
            artifact_filename=render.artifact_filename,
            operator_user_id=request.operator_user_id,
        )
    )
    operator_review = _operator_gate(
        visual_qa_result=visual_qa,
        decision=request.operator_visual_qa_decision,
        operator_user_id=request.operator_user_id,
    )

    manifest = _build_k6_manifest(request=request, render=render, planning=planning, quality=quality, provenance=provenance, visual_qa=visual_qa, operator_review=operator_review, events=tuple(events))
    artifact = K6WorkflowArtifact(
        artifact_kind="presentation_pptx",
        filename=render.artifact_filename,
        content_type=render.content_type,
        checksum_sha256=render.checksum_sha256,
        size_bytes=render.size_bytes,
    )
    gates = _build_gates(planning=planning, approved=approved, quality=quality, provenance=provenance, render=render, visual_qa=visual_qa, operator_review=operator_review)
    status = "ready_for_operator_delivery" if all(gate.status == "passed" for gate in gates) else "needs_operator_attention"
    metadata = _safe_metadata(
        request=request,
        status=status,
        planning=planning,
        approved=approved,
        quality=quality,
        provenance=provenance,
        render=render,
        visual_qa=visual_qa,
        operator_review=operator_review,
        gates=gates,
        manifest=manifest,
        events=tuple(events),
    )
    return K6EndToEndWorkflowResult(
        planning_result=planning,
        plan_editor_result=approved,
        renderer_quality_result=quality,
        provenance_result=provenance,
        render_result=render,
        visual_qa_result=visual_qa,
        operator_review=operator_review,
        workflow_artifacts=(artifact,),
        gates=gates,
        manifest=manifest,
        safe_metadata=metadata,
    )


def build_k6_capabilities_report() -> dict[str, object]:
    return {
        "mode": "k6-end-to-end-kimi-like-workflow",
        "checkpoint": K6_CHECKPOINT,
        "schema_version": K6_SCHEMA_VERSION,
        "workflow_id": K6_WORKFLOW_ID,
        "end_to_end_kimi_like_workflow_supported": True,
        "source_to_pptx_workflow_supported": True,
        "k1_planning_integrated": True,
        "k2_plan_editor_approval_integrated": True,
        "k3_renderer_quality_integrated": True,
        "k4_visual_qa_integrated": True,
        "k5_source_to_slide_provenance_integrated": True,
        "operator_gate_supported": True,
        "downloadable_artifact_supported": True,
        "safe_manifest_supported": True,
        "offline_intranet_default_supported": True,
        "direct_local_gigachat_first": True,
        "deterministic_fallback_supported": True,
        "api_endpoint_added_by_k6": False,
        "db_schema_migration_added_by_k6": False,
        "frontend_runtime_changed_by_k6": False,
        "dependency_versions_changed_by_k6": False,
        "dockerfiles_changed_by_k6": False,
        "cloud_llm_added_by_k6": False,
        "cloud_vision_added_by_k6": False,
        "internet_runtime_required_by_k6": False,
        "kimi_level_claimed_by_k6": False,
        "whole_project_kimi_level_supported": False,
    }


def validate_k6_end_to_end_result(result: K6EndToEndWorkflowResult) -> list[str]:
    errors: list[str] = []
    metadata = result.safe_metadata
    if metadata.get("checkpoint") != K6_CHECKPOINT:
        errors.append("K6 metadata checkpoint mismatch")
    if metadata.get("end_to_end_kimi_like_workflow_supported") is not True:
        errors.append("K6 workflow support flag missing")
    if result.provenance_result.coverage.coverage_status != "complete":
        errors.append("K6 requires complete K5 source-to-slide coverage")
    if result.visual_qa_result.status not in {"passed", "needs_operator_review"}:
        errors.append(f"K6 visual QA status is not deliverable: {result.visual_qa_result.status}")
    if result.operator_review.decision != "approve":
        errors.append("K6 operator gate must approve the generated deck in the smoke path")
    if result.render_result.size_bytes <= 0:
        errors.append("K6 render artifact is empty")
    if result.render_result.slide_count != len(result.provenance_result.plan.slides):
        errors.append("K6 rendered slide count does not match provenance plan")
    if not all(slide.citations for slide in result.provenance_result.plan.slides):
        errors.append("K6 every slide must carry source citations")
    if not result.manifest.get("source_to_slide_provenance"):
        errors.append("K6 manifest missing K5 source-to-slide provenance section")
    if result.manifest.get("k6_workflow", {}).get("checkpoint") != K6_CHECKPOINT:
        errors.append("K6 manifest missing workflow section")
    if metadata.get("network_required") is not False:
        errors.append("K6 must remain offline/intranet-safe by default")
    if metadata.get("kimi_level_claimed_by_k6") is not False:
        errors.append("K6 must not claim full Kimi-level")
    if metadata.get("whole_project_kimi_level_supported") is not False:
        errors.append("K6 must not mark the whole project as Kimi-level")
    if any(gate.status != "passed" for gate in result.gates):
        errors.append("K6 all workflow gates must pass in the smoke path")
    return errors


def _operator_gate(*, visual_qa_result: VisualQARuntimeResult, decision: str, operator_user_id: str) -> VisualQAOperatorReview:
    if any(issue.severity == "blocker" for issue in visual_qa_result.issues):
        return build_visual_qa_operator_review(
            VisualQAReviewRequest(
                visual_qa_result=visual_qa_result,
                decision="request_rework",
                operator_user_id=operator_user_id,
                rejection_reason="K6 automatic operator gate detected blocker visual QA issues.",
            )
        )
    safe_decision = decision if decision in {"approve", "request_rework", "reject"} else "approve"
    if safe_decision == "approve":
        return build_visual_qa_operator_review(
            VisualQAReviewRequest(
                visual_qa_result=visual_qa_result,
                decision="approve",
                operator_user_id=operator_user_id,
                accepted_issue_ids=tuple(issue.issue_id for issue in visual_qa_result.issues if issue.severity in {"warning", "info"}),
            )
        )
    return build_visual_qa_operator_review(
        VisualQAReviewRequest(
            visual_qa_result=visual_qa_result,
            decision=safe_decision,
            operator_user_id=operator_user_id,
            rejection_reason="K6 operator requested rework before delivery.",
        )
    )


def _k2_evidence_links_by_slide(plan: Any, source_refs: tuple[dict[str, Any], ...]) -> dict[str, tuple[K2EvidenceLink, ...]]:
    if not source_refs:
        return {}
    first = source_refs[0]
    link = K2EvidenceLink(
        source_id=str(first.get("source_id") or "source_001")[:80],
        title=str(first.get("title") or "Operator supplied source")[:120],
        locator=str(first.get("locator") or "")[:120] or None,
        evidence_kind="k6_source_reference",
    )
    return {slide.slide_id: (link,) for slide in plan.slides}


def _build_gates(
    *,
    planning: K1PlanningResult,
    approved: K2PlanEditorResult,
    quality: RendererQualityResult,
    provenance: K5SourceToSlideProvenanceResult,
    render: ApprovedPlanRenderResult,
    visual_qa: VisualQARuntimeResult,
    operator_review: VisualQAOperatorReview,
) -> tuple[K6WorkflowGate, ...]:
    visual_deliverable = visual_qa.status in {"passed", "needs_operator_review"} and not any(issue.severity == "blocker" for issue in visual_qa.issues)
    return (
        K6WorkflowGate("k1_plan", "passed" if len(planning.plan.slides) >= 3 else "failed", {"slide_count": len(planning.plan.slides), "fallback_used": planning.deterministic_fallback_used}),
        K6WorkflowGate("k2_approval", "passed" if approved.approved_plan is not None else "failed", {"approved_plan_present": approved.approved_plan is not None}),
        K6WorkflowGate("k3_renderer_quality", "passed" if len(quality.render_plan.slides) == len(planning.plan.slides) else "failed", {"slide_count": len(quality.render_plan.slides)}),
        K6WorkflowGate("k5_provenance", "passed" if provenance.coverage.coverage_status == "complete" else "failed", provenance.coverage.as_dict()),
        K6WorkflowGate("approved_plan_render", "passed" if render.size_bytes > 0 else "failed", {"size_bytes": render.size_bytes, "checksum_sha256": render.checksum_sha256}),
        K6WorkflowGate("k4_visual_qa", "passed" if visual_deliverable else "failed", {"status": visual_qa.status, "issue_count": len(visual_qa.issues), "score": visual_qa.score}),
        K6WorkflowGate("operator_gate", "passed" if operator_review.decision == "approve" else "failed", {"decision": operator_review.decision, "review_status": operator_review.review_status}),
    )


def _build_k6_manifest(
    *,
    request: K6EndToEndWorkflowRequest,
    render: ApprovedPlanRenderResult,
    planning: K1PlanningResult,
    quality: RendererQualityResult,
    provenance: K5SourceToSlideProvenanceResult,
    visual_qa: VisualQARuntimeResult,
    operator_review: VisualQAOperatorReview,
    events: tuple[str, ...],
) -> dict[str, object]:
    base_manifest: dict[str, object] = {
        "schema_version": "k6.end_to_end_manifest.v1",
        "workflow_id": K6_WORKFLOW_ID,
        "artifact": {
            "filename": render.artifact_filename,
            "content_type": render.content_type,
            "checksum_sha256": render.checksum_sha256,
            "size_bytes": render.size_bytes,
            "slide_count": render.slide_count,
        },
        "k6_workflow": {
            "checkpoint": K6_CHECKPOINT,
            "schema_version": K6_SCHEMA_VERSION,
            "event_types": list(events),
            "planning_prompt_digest": planning.prompt_digest,
            "source_digest": planning.source_digest,
            "render_quality_profile": quality.profile.profile_id,
            "visual_qa_status": visual_qa.status,
            "operator_decision": operator_review.decision,
            "network_required": False,
            "kimi_level_claimed_by_k6": False,
        },
        "integrity": {
            "render_checksum_sha256": render.checksum_sha256,
            "k6_manifest_payload_digest": _digest_payload(
                {
                    "render_checksum_sha256": render.checksum_sha256,
                    "source_digest": planning.source_digest,
                    "k5_section_digest": provenance.manifest_section["integrity"]["section_digest"],
                    "visual_qa_checksum": visual_qa.artifact_checksum_sha256,
                    "operator_decision": operator_review.decision,
                }
            ),
        },
    }
    return attach_k5_provenance_to_manifest(base_manifest, provenance)


def _safe_metadata(
    *,
    request: K6EndToEndWorkflowRequest,
    status: str,
    planning: K1PlanningResult,
    approved: K2PlanEditorResult,
    quality: RendererQualityResult,
    provenance: K5SourceToSlideProvenanceResult,
    render: ApprovedPlanRenderResult,
    visual_qa: VisualQARuntimeResult,
    operator_review: VisualQAOperatorReview,
    gates: tuple[K6WorkflowGate, ...],
    manifest: dict[str, object],
    events: tuple[str, ...],
) -> dict[str, object]:
    metadata: dict[str, object] = {
        **build_k6_capabilities_report(),
        "status": status,
        "k_phase_branch": K_PHASE_BRANCH,
        "base_after_k5": K6_BASE_AFTER_K5,
        "session_id": request.session_id,
        "task_id": request.task_id,
        "presentation_id": request.presentation_id,
        "operator_user_id": _safe_short_text(request.operator_user_id, 80),
        "slide_count": render.slide_count,
        "artifact_filename": render.artifact_filename,
        "artifact_checksum_sha256": render.checksum_sha256,
        "artifact_size_bytes": render.size_bytes,
        "render_mode": render.render_mode,
        "template_id": render.template_id,
        "k1_llm_used": planning.llm_used,
        "k1_deterministic_fallback_used": planning.deterministic_fallback_used,
        "k2_approved_plan_present": approved.approved_plan is not None,
        "k3_render_quality_slide_count": len(quality.slide_results),
        "k5_coverage_status": provenance.coverage.coverage_status,
        "k5_slide_evidence_link_count": len(provenance.slide_links),
        "k4_visual_qa_status": visual_qa.status,
        "k4_visual_qa_score": visual_qa.score,
        "operator_review_status": operator_review.review_status,
        "operator_decision": operator_review.decision,
        "gate_count": len(gates),
        "passed_gate_count": sum(1 for gate in gates if gate.status == "passed"),
        "gate_statuses": {gate.gate_id: gate.status for gate in gates},
        "event_types": events,
        "manifest_digest": manifest.get("integrity", {}).get("k6_manifest_payload_digest"),
        "k5_section_digest": manifest.get("integrity", {}).get("k5_source_to_slide_section_digest"),
        "raw_source_text_stored": False,
        "raw_prompt_stored": False,
        "raw_sensitive_values_stored": False,
        "network_required": False,
        "internet_runtime_required_by_k6": False,
        "kimi_level_claimed_by_k6": False,
        "whole_project_kimi_level_supported": False,
    }
    _assert_safe_payload(metadata, source_text=request.source_text)
    return metadata


def _validate_request(request: K6EndToEndWorkflowRequest) -> None:
    if not request.source_text.strip():
        raise ValueError("K6 workflow requires source_text")
    if request.target_slide_count < 5 or request.target_slide_count > 10:
        raise ValueError("K6 target_slide_count must be between 5 and 10")
    if request.render_mode not in {"adaptive", "template"}:
        raise ValueError(f"Unsupported K6 render_mode: {request.render_mode!r}")
    if not request.template_id.strip():
        raise ValueError("K6 workflow requires an explicit local template_id")
    if request.operator_visual_qa_decision not in {"approve", "request_rework", "reject"}:
        raise ValueError("K6 operator_visual_qa_decision must be approve, request_rework, or reject")


def _string_source_ref(ref: dict[str, Any]) -> dict[str, str]:
    return {str(key): _safe_short_text(value, 160) for key, value in ref.items() if value is not None}


def _stable_id(prefix: str, *parts: object) -> str:
    return prefix + "_" + sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]


def _digest_payload(payload: dict[str, Any]) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _safe_short_text(value: object, limit: int) -> str:
    cleaned = " ".join(str(value or "").replace("\n", " ").split())
    return cleaned[:limit]


def _assert_safe_payload(payload: dict[str, object], *, source_text: str) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).lower()
    if source_text[:80].lower() in encoded:
        raise RuntimeError("K6 safe metadata contains raw source text")
    for forbidden in _FORBIDDEN_SAFE_TEXT:
        if forbidden in encoded:
            raise RuntimeError("K6 safe metadata contains forbidden secret-like value")
