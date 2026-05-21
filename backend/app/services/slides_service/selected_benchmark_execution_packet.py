from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.kimi_style_benchmark import (
    ACCEPTED_FINAL_CLAIM_WORDING,
    REQUIRED_AUTOMATED_EVIDENCE,
    REQUIRED_HUMAN_REVIEW_DIMENSIONS,
    REQUIRED_S_PHASE_EVIDENCE,
    S10_SCENARIO_IDS,
    kimi_style_benchmark_report,
)
from backend.app.services.slides_service.s_phase_closure import s_phase_closure_report

S12_WORKFLOW_ID = "slides.selected_benchmark_execution_packet"
INITIAL_REVIEW_STATE = "pending_human_review"
ALLOWED_REVIEW_DECISIONS = ("approve", "request_rework", "reject")
REVIEW_PACKET_COMPONENTS = (
    "scenario_execution_manifest",
    "scenario_evidence_manifest",
    "human_review_worksheets",
    "reviewer_instructions",
    "review_result_ingest_schema",
    "operator_handoff_readme",
)
REQUIRED_WORKSHEET_FIELDS = (
    "worksheet_id",
    "scenario_id",
    "reviewer_id",
    "reviewed_at",
    "decision",
    "scores",
    "slide_level_findings",
    "visual_defects",
    "citation_findings",
    "follow_up_backlog",
    "claim_safety_acknowledgement",
)
REQUIRED_EVIDENCE_MANIFEST_FIELDS = (
    "scenario_id",
    "source_packet_id",
    "approved_plan_snapshot_id",
    "generated_pptx_id",
    "artifact_manifest_id",
    "safe_metadata_id",
    "citation_manifest_id",
    "render_geometry_manifest_id",
    "render_based_visual_qa_report_id",
    "human_review_worksheet_id",
)
FORBIDDEN_S12_ACTIONS = (
    "auto_approve_benchmark_results",
    "fabricate_human_review_results",
    "claim_selected_parity_without_completed_results",
    "claim_kimi_level_achieved",
    "claim_server3_local_intranet_verified",
    "use_hidden_public_internet",
    "use_cloud_research",
    "use_cloud_vision",
)


@dataclass(frozen=True)
class SelectedBenchmarkScenarioPacket:
    scenario_id: str
    required_s_phase_evidence: tuple[str, ...]
    required_automated_outputs: tuple[str, ...]
    required_human_review_dimensions: tuple[str, ...]
    required_worksheet_fields: tuple[str, ...]
    required_evidence_manifest_fields: tuple[str, ...]
    initial_review_state: str = INITIAL_REVIEW_STATE
    human_review_required: bool = True
    auto_approval_allowed: bool = False
    offline_ready: bool = True
    public_internet_required: bool = False
    cloud_research_allowed: bool = False
    cloud_vision_allowed: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "required_s_phase_evidence",
            "required_automated_outputs",
            "required_human_review_dimensions",
            "required_worksheet_fields",
            "required_evidence_manifest_fields",
        ):
            payload[key] = list(payload[key])
        return payload


def build_scenario_packets() -> tuple[SelectedBenchmarkScenarioPacket, ...]:
    return tuple(
        SelectedBenchmarkScenarioPacket(
            scenario_id=scenario_id,
            required_s_phase_evidence=REQUIRED_S_PHASE_EVIDENCE,
            required_automated_outputs=REQUIRED_AUTOMATED_EVIDENCE,
            required_human_review_dimensions=REQUIRED_HUMAN_REVIEW_DIMENSIONS,
            required_worksheet_fields=REQUIRED_WORKSHEET_FIELDS,
            required_evidence_manifest_fields=REQUIRED_EVIDENCE_MANIFEST_FIELDS,
        )
        for scenario_id in S10_SCENARIO_IDS
    )


SCENARIO_PACKETS = build_scenario_packets()


def validate_selected_benchmark_execution_packet() -> list[str]:
    errors: list[str] = []
    s10 = kimi_style_benchmark_report()
    s11 = s_phase_closure_report()
    if s10.get("status") != "ready":
        errors.append("S12 requires S10 benchmark contract to be ready")
    if s11.get("status") != "ready":
        errors.append("S12 requires S11 S-phase closure to be ready")
    if len(SCENARIO_PACKETS) != 12:
        errors.append(f"S12 must prepare exactly 12 scenario packets, got {len(SCENARIO_PACKETS)}")
    packet_by_id = {packet.scenario_id: packet for packet in SCENARIO_PACKETS}
    for scenario_id in S10_SCENARIO_IDS:
        packet = packet_by_id.get(scenario_id)
        if packet is None:
            errors.append(f"missing S12 scenario packet: {scenario_id}")
            continue
        if packet.initial_review_state != INITIAL_REVIEW_STATE:
            errors.append(f"{scenario_id}: initial review state must be pending_human_review")
        if packet.auto_approval_allowed:
            errors.append(f"{scenario_id}: auto approval must not be allowed")
        if not packet.human_review_required:
            errors.append(f"{scenario_id}: human review must be required")
        if not packet.offline_ready or packet.public_internet_required:
            errors.append(f"{scenario_id}: offline boundary is invalid")
        if packet.cloud_research_allowed or packet.cloud_vision_allowed:
            errors.append(f"{scenario_id}: cloud research/vision must not be allowed")
        for value in REQUIRED_S_PHASE_EVIDENCE:
            if value not in packet.required_s_phase_evidence:
                errors.append(f"{scenario_id}: missing S-phase evidence {value}")
        for value in REQUIRED_AUTOMATED_EVIDENCE:
            if value not in packet.required_automated_outputs:
                errors.append(f"{scenario_id}: missing automated output {value}")
        for value in REQUIRED_HUMAN_REVIEW_DIMENSIONS:
            if value not in packet.required_human_review_dimensions:
                errors.append(f"{scenario_id}: missing review dimension {value}")
        for value in REQUIRED_WORKSHEET_FIELDS:
            if value not in packet.required_worksheet_fields:
                errors.append(f"{scenario_id}: missing worksheet field {value}")
        for value in REQUIRED_EVIDENCE_MANIFEST_FIELDS:
            if value not in packet.required_evidence_manifest_fields:
                errors.append(f"{scenario_id}: missing evidence manifest field {value}")
    return errors


def selected_benchmark_execution_packet_report() -> dict[str, Any]:
    errors = validate_selected_benchmark_execution_packet()
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S12_WORKFLOW_ID,
        "s_phase": "S12",
        "selected_benchmark_execution_packet_completed_by_s12": not errors,
        "scenario_packet_count": len(SCENARIO_PACKETS),
        "scenario_ids": [packet.scenario_id for packet in SCENARIO_PACKETS],
        "review_packet_components": list(REVIEW_PACKET_COMPONENTS),
        "worksheet_count_required_by_s12": len(SCENARIO_PACKETS),
        "human_review_worksheets_required_by_s12": True,
        "evidence_manifest_required_by_s12": True,
        "review_result_ingest_schema_required_by_s12": True,
        "reviewer_instructions_required_by_s12": True,
        "initial_review_state_by_s12": INITIAL_REVIEW_STATE,
        "completed_human_review_required_before_selected_parity_claim_by_s12": True,
        "completed_human_review_results_present_by_s12": False,
        "human_review_results_fabricated_by_s12": False,
        "auto_approval_allowed_by_s12": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s12": False,
        "selected_offline_workflow_parity_claim_requires_future_completed_results_by_s12": True,
        "accepted_future_claim_wording_by_s12": ACCEPTED_FINAL_CLAIM_WORDING,
        "generic_kimi_level_achieved_claim_allowed_by_s12": False,
        "kimi_level_claimed_by_s12": False,
        "whole_project_kimi_level_supported": False,
        "server3_local_intranet_route_verified_by_s12": False,
        "hidden_public_internet_allowed_by_s12": False,
        "cloud_research_allowed_by_s12": False,
        "cloud_vision_allowed_by_s12": False,
        "public_internet_required_by_s12": False,
        "offline_ready_by_s12": True,
        "api_endpoint_added_by_s12": False,
        "db_schema_migration_added_by_s12": False,
        "frontend_runtime_changed_by_s12": False,
        "dependency_versions_changed_by_s12": False,
        "dockerfiles_changed_by_s12": False,
        "next_recommended_step": "Execute S12 benchmark packet, generate 12 evidence packets, and collect real completed human review results before any selected parity claim.",
        "contract": {
            "scenario_packets": [packet.as_dict() for packet in SCENARIO_PACKETS],
            "allowed_review_decisions": list(ALLOWED_REVIEW_DECISIONS),
            "review_packet_components": list(REVIEW_PACKET_COMPONENTS),
            "forbidden_actions": list(FORBIDDEN_S12_ACTIONS),
        },
        "errors": errors,
    }
