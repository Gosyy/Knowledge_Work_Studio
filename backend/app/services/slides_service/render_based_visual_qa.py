from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

S9_WORKFLOW_ID = "slides.render_based_visual_qa"

REQUIRED_RENDER_EVIDENCE = (
    "rendered_slide_screenshot",
    "slide_geometry_manifest",
    "native_visual_geometry_manifest",
    "image_region_reconstruction_manifest",
    "citation_manifest",
    "revised_plan_snapshot_metadata",
)

REQUIRED_VISUAL_CHECKS = (
    "title_body_collision",
    "text_box_overlap",
    "clipped_text",
    "tiny_text",
    "table_overflow",
    "dense_native_visual_region",
    "chart_label_collision",
    "diagram_node_overlap",
    "image_reconstruction_mismatch",
    "citation_marker_visibility",
)

SUPPORTED_DEFECT_SEVERITIES = ("info", "warning", "blocker")

REQUIRED_COMPATIBILITY_TARGETS = (
    "s3_adaptive_deck_modes",
    "s4_native_table_chart_diagram_rendering",
    "s6_image_screenshot_to_slide_workflow",
    "s7_offline_intranet_research_citations",
    "s8_conversational_edit_loop",
)

SAFE_TASK_EVENTS = (
    "slides.visual_qa.render_requested",
    "slides.visual_qa.render_completed",
    "slides.visual_qa.geometry_manifest_loaded",
    "slides.visual_qa.native_visuals_checked",
    "slides.visual_qa.image_regions_checked",
    "slides.visual_qa.citations_checked",
    "slides.visual_qa.defects_reported",
    "slides.visual_qa.completed",
)

FORBIDDEN_RENDER_QA_SOURCES = (
    "cloud_vision_result",
    "hidden_public_web_lookup",
    "remote_screenshot_service",
    "unattributed_model_memory",
)


@dataclass(frozen=True)
class RenderBasedVisualCheckPolicy:
    check_id: str
    requires_rendered_slide: bool = True
    requires_geometry: bool = True
    produces_slide_level_defect: bool = True
    supports_blocker_severity: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RenderBasedVisualQaContract:
    workflow_id: str
    title: str
    required_render_evidence: tuple[str, ...]
    required_visual_checks: tuple[str, ...]
    supported_defect_severities: tuple[str, ...]
    compatibility_targets: tuple[str, ...]
    safe_task_events: tuple[str, ...]
    forbidden_sources: tuple[str, ...]
    check_policies: tuple[RenderBasedVisualCheckPolicy, ...]
    actual_slide_render_required: bool
    geometry_manifest_required: bool
    native_visual_geometry_required: bool
    image_region_geometry_required: bool
    citation_manifest_required: bool
    slide_level_defect_report_required: bool
    blocker_defect_can_fail_release_gate: bool
    visual_qa_score_alone_can_approve: bool
    semantic_qa_alone_can_approve: bool
    offline_ready: bool
    provenance_required: bool
    compatible_with_s3_modes: bool
    compatible_with_s4_native_visuals: bool
    compatible_with_s6_image_regions: bool
    compatible_with_s7_citations: bool
    compatible_with_s8_conversational_edits: bool
    cloud_vision_allowed: bool
    hidden_public_internet_allowed: bool
    browser_runtime_required: bool
    kimi_level_claimed: bool
    server3_local_intranet_verified: bool

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["required_render_evidence"] = list(self.required_render_evidence)
        payload["required_visual_checks"] = list(self.required_visual_checks)
        payload["supported_defect_severities"] = list(self.supported_defect_severities)
        payload["compatibility_targets"] = list(self.compatibility_targets)
        payload["safe_task_events"] = list(self.safe_task_events)
        payload["forbidden_sources"] = list(self.forbidden_sources)
        payload["check_policies"] = [policy.as_dict() for policy in self.check_policies]
        return payload


CHECK_POLICIES = tuple(RenderBasedVisualCheckPolicy(check_id=check_id) for check_id in REQUIRED_VISUAL_CHECKS)

RENDER_BASED_VISUAL_QA_CONTRACT = RenderBasedVisualQaContract(
    workflow_id=S9_WORKFLOW_ID,
    title="Render-based visual QA for actual slide screenshots and geometry manifests",
    required_render_evidence=REQUIRED_RENDER_EVIDENCE,
    required_visual_checks=REQUIRED_VISUAL_CHECKS,
    supported_defect_severities=SUPPORTED_DEFECT_SEVERITIES,
    compatibility_targets=REQUIRED_COMPATIBILITY_TARGETS,
    safe_task_events=SAFE_TASK_EVENTS,
    forbidden_sources=FORBIDDEN_RENDER_QA_SOURCES,
    check_policies=CHECK_POLICIES,
    actual_slide_render_required=True,
    geometry_manifest_required=True,
    native_visual_geometry_required=True,
    image_region_geometry_required=True,
    citation_manifest_required=True,
    slide_level_defect_report_required=True,
    blocker_defect_can_fail_release_gate=True,
    visual_qa_score_alone_can_approve=False,
    semantic_qa_alone_can_approve=False,
    offline_ready=True,
    provenance_required=True,
    compatible_with_s3_modes=True,
    compatible_with_s4_native_visuals=True,
    compatible_with_s6_image_regions=True,
    compatible_with_s7_citations=True,
    compatible_with_s8_conversational_edits=True,
    cloud_vision_allowed=False,
    hidden_public_internet_allowed=False,
    browser_runtime_required=False,
    kimi_level_claimed=False,
    server3_local_intranet_verified=False,
)


def validate_render_based_visual_qa_contract(contract: RenderBasedVisualQaContract = RENDER_BASED_VISUAL_QA_CONTRACT) -> list[str]:
    errors: list[str] = []
    if contract.workflow_id != S9_WORKFLOW_ID:
        errors.append("workflow_id must be slides.render_based_visual_qa")
    for evidence in REQUIRED_RENDER_EVIDENCE:
        if evidence not in contract.required_render_evidence:
            errors.append(f"missing render evidence: {evidence}")
    for check_id in REQUIRED_VISUAL_CHECKS:
        if check_id not in contract.required_visual_checks:
            errors.append(f"missing visual check: {check_id}")
    for severity in SUPPORTED_DEFECT_SEVERITIES:
        if severity not in contract.supported_defect_severities:
            errors.append(f"missing defect severity: {severity}")
    for target in REQUIRED_COMPATIBILITY_TARGETS:
        if target not in contract.compatibility_targets:
            errors.append(f"missing compatibility target: {target}")
    for event in SAFE_TASK_EVENTS:
        if event not in contract.safe_task_events:
            errors.append(f"missing safe task event: {event}")
    for source in FORBIDDEN_RENDER_QA_SOURCES:
        if source not in contract.forbidden_sources:
            errors.append(f"missing forbidden render QA source: {source}")
    must_be_true = {
        "actual_slide_render_required": contract.actual_slide_render_required,
        "geometry_manifest_required": contract.geometry_manifest_required,
        "native_visual_geometry_required": contract.native_visual_geometry_required,
        "image_region_geometry_required": contract.image_region_geometry_required,
        "citation_manifest_required": contract.citation_manifest_required,
        "slide_level_defect_report_required": contract.slide_level_defect_report_required,
        "blocker_defect_can_fail_release_gate": contract.blocker_defect_can_fail_release_gate,
        "offline_ready": contract.offline_ready,
        "provenance_required": contract.provenance_required,
        "compatible_with_s3_modes": contract.compatible_with_s3_modes,
        "compatible_with_s4_native_visuals": contract.compatible_with_s4_native_visuals,
        "compatible_with_s6_image_regions": contract.compatible_with_s6_image_regions,
        "compatible_with_s7_citations": contract.compatible_with_s7_citations,
        "compatible_with_s8_conversational_edits": contract.compatible_with_s8_conversational_edits,
    }
    for name, value in must_be_true.items():
        if value is not True:
            errors.append(f"{name} must be true")
    must_be_false = {
        "visual_qa_score_alone_can_approve": contract.visual_qa_score_alone_can_approve,
        "semantic_qa_alone_can_approve": contract.semantic_qa_alone_can_approve,
        "cloud_vision_allowed": contract.cloud_vision_allowed,
        "hidden_public_internet_allowed": contract.hidden_public_internet_allowed,
        "browser_runtime_required": contract.browser_runtime_required,
        "kimi_level_claimed": contract.kimi_level_claimed,
        "server3_local_intranet_verified": contract.server3_local_intranet_verified,
    }
    for name, value in must_be_false.items():
        if value is not False:
            errors.append(f"{name} must be false")
    for policy in contract.check_policies:
        if policy.check_id not in REQUIRED_VISUAL_CHECKS:
            errors.append(f"unknown check policy: {policy.check_id}")
        if not policy.requires_rendered_slide:
            errors.append(f"{policy.check_id} must require rendered slide evidence")
        if not policy.requires_geometry:
            errors.append(f"{policy.check_id} must require geometry evidence")
        if not policy.produces_slide_level_defect:
            errors.append(f"{policy.check_id} must produce slide-level defect evidence")
        if not policy.supports_blocker_severity:
            errors.append(f"{policy.check_id} must support blocker severity")
    return errors


def render_based_visual_qa_report() -> dict[str, Any]:
    contract = RENDER_BASED_VISUAL_QA_CONTRACT
    errors = validate_render_based_visual_qa_contract(contract)
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S9_WORKFLOW_ID,
        "s_phase": "S9",
        "render_based_visual_qa_completed_by_s9": not errors,
        "actual_slide_render_required_by_s9": contract.actual_slide_render_required,
        "geometry_manifest_required_by_s9": contract.geometry_manifest_required,
        "native_visual_geometry_required_by_s9": contract.native_visual_geometry_required,
        "image_region_geometry_required_by_s9": contract.image_region_geometry_required,
        "citation_manifest_required_by_s9": contract.citation_manifest_required,
        "slide_level_defect_report_required_by_s9": contract.slide_level_defect_report_required,
        "blocker_defect_can_fail_release_gate_by_s9": contract.blocker_defect_can_fail_release_gate,
        "visual_qa_score_alone_can_approve_by_s9": contract.visual_qa_score_alone_can_approve,
        "semantic_qa_alone_can_approve_by_s9": contract.semantic_qa_alone_can_approve,
        "required_visual_check_count": len(contract.required_visual_checks),
        "required_visual_checks": list(contract.required_visual_checks),
        "required_render_evidence": list(contract.required_render_evidence),
        "compatible_with_s3_modes_by_s9": contract.compatible_with_s3_modes,
        "compatible_with_s4_native_visuals_by_s9": contract.compatible_with_s4_native_visuals,
        "compatible_with_s6_image_regions_by_s9": contract.compatible_with_s6_image_regions,
        "compatible_with_s7_citations_by_s9": contract.compatible_with_s7_citations,
        "compatible_with_s8_conversational_edits_by_s9": contract.compatible_with_s8_conversational_edits,
        "cloud_vision_allowed_by_s9": contract.cloud_vision_allowed,
        "hidden_public_internet_allowed_by_s9": contract.hidden_public_internet_allowed,
        "public_internet_required_by_s9": False,
        "browser_runtime_required_by_s9": contract.browser_runtime_required,
        "offline_ready_by_s9": contract.offline_ready,
        "api_endpoint_added_by_s9": False,
        "db_schema_migration_added_by_s9": False,
        "frontend_runtime_changed_by_s9": False,
        "dependency_versions_changed_by_s9": False,
        "dockerfiles_changed_by_s9": False,
        "kimi_level_claimed_by_s9": contract.kimi_level_claimed,
        "whole_project_kimi_level_supported": False,
        "server3_local_intranet_route_verified_by_s9": contract.server3_local_intranet_verified,
        "next_recommended_step": "S10 - expanded Kimi-style benchmark and human review for selected offline workflow parity scenarios.",
        "contract": contract.as_dict(),
        "errors": errors,
    }
