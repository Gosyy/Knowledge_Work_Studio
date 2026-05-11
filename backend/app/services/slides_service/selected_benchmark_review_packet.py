
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.kimi_style_benchmark import (
    ACCEPTED_FINAL_CLAIM_WORDING,
    REQUIRED_AUTOMATED_EVIDENCE,
    REQUIRED_HUMAN_REVIEW_DIMENSIONS,
    REQUIRED_S_PHASE_EVIDENCE,
    S10_SCENARIO_IDS,
)
from backend.app.services.slides_service.selected_benchmark_execution_packet import (
    INITIAL_REVIEW_STATE,
    REQUIRED_EVIDENCE_MANIFEST_FIELDS,
    REQUIRED_WORKSHEET_FIELDS,
    selected_benchmark_execution_packet_report,
)

S13A_WORKFLOW_ID = "slides.selected_benchmark_review_packet_skeleton"
S13A_PHASE_ID = "S13a"

REVIEW_PACKET_SKELETON_COMPONENTS = (
    "packet_index_json",
    "scenario_execution_manifest_json",
    "scenario_evidence_manifest_json",
    "human_review_worksheet_json",
    "reviewer_instructions_markdown",
    "operator_handoff_readme_markdown",
    "review_result_ingest_schema_json",
)

REQUIRED_PACKET_INDEX_FIELDS = (
    "packet_id",
    "scenario_id",
    "execution_state",
    "review_state",
    "worksheet_id",
    "evidence_manifest_id",
    "accepted_future_claim_wording",
)

EXECUTION_STATES = (
    "packet_skeleton_ready",
    "awaiting_live_generation",
    "generated_artifacts_ready",
    "human_review_pending",
    "human_review_completed",
)

FORBIDDEN_S13A_ACTIONS = (
    "run_live_gigachat_generation",
    "fabricate_human_review_results",
    "auto_approve_scenarios",
    "claim_selected_offline_workflow_parity",
    "claim_kimi_level_achieved",
    "claim_server3_local_intranet_verified",
    "use_hidden_public_internet",
    "use_cloud_research",
    "use_cloud_vision",
)


@dataclass(frozen=True)
class ScenarioReviewPacketSkeleton:
    scenario_id: str
    packet_id: str
    worksheet_id: str
    evidence_manifest_id: str
    execution_state: str
    review_state: str
    required_packet_index_fields: tuple[str, ...]
    required_evidence_manifest_fields: tuple[str, ...]
    required_worksheet_fields: tuple[str, ...]
    required_s_phase_evidence: tuple[str, ...]
    required_automated_evidence: tuple[str, ...]
    required_human_review_dimensions: tuple[str, ...]
    review_packet_components: tuple[str, ...]
    accepted_future_claim_wording: str
    live_gigachat_required_for_skeleton: bool = False
    public_api_dev_execution_performed: bool = False
    completed_human_review_results_present: bool = False
    auto_approval_allowed: bool = False
    selected_parity_claim_supported_now: bool = False
    offline_ready: bool = True
    hidden_public_internet_allowed: bool = False
    cloud_research_allowed: bool = False
    cloud_vision_allowed: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "required_packet_index_fields",
            "required_evidence_manifest_fields",
            "required_worksheet_fields",
            "required_s_phase_evidence",
            "required_automated_evidence",
            "required_human_review_dimensions",
            "review_packet_components",
        ):
            payload[key] = list(payload[key])
        return payload


def build_review_packet_skeletons() -> tuple[ScenarioReviewPacketSkeleton, ...]:
    return tuple(
        ScenarioReviewPacketSkeleton(
            scenario_id=scenario_id,
            packet_id=f"s13a_packet_{index:02d}_{scenario_id}",
            worksheet_id=f"s13a_worksheet_{index:02d}_{scenario_id}",
            evidence_manifest_id=f"s13a_evidence_{index:02d}_{scenario_id}",
            execution_state="packet_skeleton_ready",
            review_state=INITIAL_REVIEW_STATE,
            required_packet_index_fields=REQUIRED_PACKET_INDEX_FIELDS,
            required_evidence_manifest_fields=REQUIRED_EVIDENCE_MANIFEST_FIELDS,
            required_worksheet_fields=REQUIRED_WORKSHEET_FIELDS,
            required_s_phase_evidence=REQUIRED_S_PHASE_EVIDENCE,
            required_automated_evidence=REQUIRED_AUTOMATED_EVIDENCE,
            required_human_review_dimensions=REQUIRED_HUMAN_REVIEW_DIMENSIONS,
            review_packet_components=REVIEW_PACKET_SKELETON_COMPONENTS,
            accepted_future_claim_wording=ACCEPTED_FINAL_CLAIM_WORDING,
        )
        for index, scenario_id in enumerate(S10_SCENARIO_IDS, start=1)
    )


REVIEW_PACKET_SKELETONS = build_review_packet_skeletons()


def validate_selected_benchmark_review_packet_skeleton() -> list[str]:
    errors: list[str] = []
    s12 = selected_benchmark_execution_packet_report()
    if s12.get("status") != "ready":
        errors.append("S13a requires S12 execution packet workflow to be ready")
    if s12.get("scenario_packet_count") != 12:
        errors.append("S13a requires 12 S12 scenario packets")
    if s12.get("completed_human_review_results_present_by_s12") is not False:
        errors.append("S13a must start before completed human review results are present")
    if s12.get("human_review_results_fabricated_by_s12") is not False:
        errors.append("S13a requires S12 to forbid fabricated human review results")
    if len(REVIEW_PACKET_SKELETONS) != 12:
        errors.append(f"S13a must prepare exactly 12 review packet skeletons, got {len(REVIEW_PACKET_SKELETONS)}")

    seen_packet_ids: set[str] = set()
    seen_worksheet_ids: set[str] = set()
    by_scenario = {packet.scenario_id: packet for packet in REVIEW_PACKET_SKELETONS}
    for scenario_id in S10_SCENARIO_IDS:
        packet = by_scenario.get(scenario_id)
        if packet is None:
            errors.append(f"missing S13a review packet skeleton: {scenario_id}")
            continue
        if packet.packet_id in seen_packet_ids:
            errors.append(f"duplicate packet_id: {packet.packet_id}")
        seen_packet_ids.add(packet.packet_id)
        if packet.worksheet_id in seen_worksheet_ids:
            errors.append(f"duplicate worksheet_id: {packet.worksheet_id}")
        seen_worksheet_ids.add(packet.worksheet_id)
        if packet.execution_state != "packet_skeleton_ready":
            errors.append(f"{scenario_id}: execution state must be packet_skeleton_ready")
        if packet.review_state != INITIAL_REVIEW_STATE:
            errors.append(f"{scenario_id}: review state must be pending_human_review")
        for field in REQUIRED_PACKET_INDEX_FIELDS:
            if field not in packet.required_packet_index_fields:
                errors.append(f"{scenario_id}: missing packet index field {field}")
        for field in REQUIRED_EVIDENCE_MANIFEST_FIELDS:
            if field not in packet.required_evidence_manifest_fields:
                errors.append(f"{scenario_id}: missing evidence manifest field {field}")
        for field in REQUIRED_WORKSHEET_FIELDS:
            if field not in packet.required_worksheet_fields:
                errors.append(f"{scenario_id}: missing worksheet field {field}")
        for evidence in REQUIRED_S_PHASE_EVIDENCE:
            if evidence not in packet.required_s_phase_evidence:
                errors.append(f"{scenario_id}: missing S-phase evidence {evidence}")
        for output in REQUIRED_AUTOMATED_EVIDENCE:
            if output not in packet.required_automated_evidence:
                errors.append(f"{scenario_id}: missing automated evidence {output}")
        for dimension in REQUIRED_HUMAN_REVIEW_DIMENSIONS:
            if dimension not in packet.required_human_review_dimensions:
                errors.append(f"{scenario_id}: missing human review dimension {dimension}")
        for component in REVIEW_PACKET_SKELETON_COMPONENTS:
            if component not in packet.review_packet_components:
                errors.append(f"{scenario_id}: missing review packet component {component}")
        if packet.accepted_future_claim_wording != ACCEPTED_FINAL_CLAIM_WORDING:
            errors.append(f"{scenario_id}: accepted future claim wording mismatch")
        if packet.live_gigachat_required_for_skeleton:
            errors.append(f"{scenario_id}: live GigaChat must not be required for skeleton generation")
        if packet.public_api_dev_execution_performed:
            errors.append(f"{scenario_id}: S13a must not perform public_api_dev execution")
        if packet.completed_human_review_results_present:
            errors.append(f"{scenario_id}: S13a must not contain completed review results")
        if packet.auto_approval_allowed:
            errors.append(f"{scenario_id}: auto approval must not be allowed")
        if packet.selected_parity_claim_supported_now:
            errors.append(f"{scenario_id}: selected parity claim must not be supported now")
        if not packet.offline_ready:
            errors.append(f"{scenario_id}: offline_ready must be true")
        if packet.hidden_public_internet_allowed or packet.cloud_research_allowed or packet.cloud_vision_allowed:
            errors.append(f"{scenario_id}: hidden internet/cloud scope must not be allowed")
    return errors


def selected_benchmark_review_packet_skeleton_report() -> dict[str, Any]:
    errors = validate_selected_benchmark_review_packet_skeleton()
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S13A_WORKFLOW_ID,
        "s_phase": S13A_PHASE_ID,
        "selected_benchmark_review_packet_skeleton_completed_by_s13a": not errors,
        "scenario_review_packet_count": len(REVIEW_PACKET_SKELETONS),
        "worksheet_count_required_by_s13a": len(REVIEW_PACKET_SKELETONS),
        "review_packet_components": list(REVIEW_PACKET_SKELETON_COMPONENTS),
        "required_packet_index_fields": list(REQUIRED_PACKET_INDEX_FIELDS),
        "initial_execution_state_by_s13a": "packet_skeleton_ready",
        "initial_review_state_by_s13a": INITIAL_REVIEW_STATE,
        "live_gigachat_required_by_s13a": False,
        "public_api_dev_execution_performed_by_s13a": False,
        "completed_human_review_results_present_by_s13a": False,
        "human_review_results_fabricated_by_s13a": False,
        "auto_approval_allowed_by_s13a": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13a": False,
        "selected_offline_workflow_parity_claim_requires_future_completed_results_by_s13a": True,
        "accepted_future_claim_wording_by_s13a": ACCEPTED_FINAL_CLAIM_WORDING,
        "hidden_public_internet_allowed_by_s13a": False,
        "cloud_research_allowed_by_s13a": False,
        "cloud_vision_allowed_by_s13a": False,
        "public_internet_required_by_s13a": False,
        "offline_ready_by_s13a": True,
        "kimi_level_claimed_by_s13a": False,
        "whole_project_kimi_level_supported": False,
        "server3_local_intranet_route_verified_by_s13a": False,
        "api_endpoint_added_by_s13a": False,
        "db_schema_migration_added_by_s13a": False,
        "frontend_runtime_changed_by_s13a": False,
        "dependency_versions_changed_by_s13a": False,
        "dockerfiles_changed_by_s13a": False,
        "next_recommended_step": "S13b - execute live public_api_dev GigaChat generation for the 12 selected benchmark scenarios.",
        "contract": {
            "execution_states": list(EXECUTION_STATES),
            "forbidden_actions": list(FORBIDDEN_S13A_ACTIONS),
            "review_packet_skeletons": [packet.as_dict() for packet in REVIEW_PACKET_SKELETONS],
        },
        "errors": errors,
    }
