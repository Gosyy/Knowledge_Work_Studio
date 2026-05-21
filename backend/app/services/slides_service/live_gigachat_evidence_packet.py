from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.kimi_style_benchmark import (
    ACCEPTED_FINAL_CLAIM_WORDING,
    S10_SCENARIO_IDS,
)
from backend.app.services.slides_service.live_gigachat_selected_benchmark import (
    PUBLIC_API_DEV_ROUTE,
    REQUIRED_PROVIDER,
    live_gigachat_selected_benchmark_report,
)
from backend.app.services.slides_service.selected_benchmark_review_packet import (
    INITIAL_REVIEW_STATE,
    REQUIRED_PACKET_INDEX_FIELDS,
    selected_benchmark_review_packet_skeleton_report,
)

S13C_WORKFLOW_ID = "slides.live_gigachat_evidence_packet_export"
S13C_PHASE_ID = "S13c"
EVIDENCE_PACKET_STATE = "live_evidence_packet_ready"

REQUIRED_LIVE_INPUTS = (
    "s13b_live_generation_manifest_json",
    "scenario_model_response_json",
    "scenario_response_digest",
    "public_api_dev_route_summary",
    "credential_safety_summary",
)

REQUIRED_EVIDENCE_PACKET_COMPONENTS = (
    "packet_index_json",
    "scenario_evidence_packet_json",
    "scenario_response_summary_json",
    "human_review_worksheet_json",
    "reviewer_instructions_markdown",
    "operator_handoff_readme_markdown",
    "archive_manifest_json",
)

REQUIRED_SCENARIO_EVIDENCE_FIELDS = (
    "scenario_id",
    "provider",
    "route",
    "model",
    "live_generation_manifest_id",
    "scenario_model_response_id",
    "model_response_digest",
    "model_response_text_present",
    "response_text_length",
    "worksheet_id",
    "review_state",
    "evidence_packet_state",
    "credential_values_recorded",
    "server3_local_intranet_verified",
    "completed_human_review_results_present",
    "selected_parity_claim_supported_now",
)

FORBIDDEN_S13C_ACTIONS = (
    "run_live_gigachat_generation_again",
    "record_raw_credential_values",
    "fabricate_human_review_results",
    "auto_approve_scenarios",
    "claim_selected_offline_workflow_parity",
    "claim_kimi_level_achieved",
    "claim_server3_local_intranet_verified",
)


@dataclass(frozen=True)
class LiveGigaChatEvidencePacketSpec:
    scenario_id: str
    provider: str
    route: str
    evidence_packet_state: str
    review_state: str
    required_live_inputs: tuple[str, ...]
    required_packet_components: tuple[str, ...]
    required_packet_index_fields: tuple[str, ...]
    required_scenario_evidence_fields: tuple[str, ...]
    accepted_future_claim_wording: str
    live_generation_must_already_exist: bool = True
    live_generation_performed_by_s13c: bool = False
    credential_values_recorded: bool = False
    raw_model_response_allowed_in_packet: bool = True
    response_digest_required: bool = True
    completed_human_review_results_present: bool = False
    human_review_results_fabricated: bool = False
    auto_approval_allowed: bool = False
    selected_parity_claim_supported_now: bool = False
    public_api_dev_route_is_not_server3_proof: bool = True
    server3_local_intranet_verified: bool = False
    kimi_level_claimed: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "required_live_inputs",
            "required_packet_components",
            "required_packet_index_fields",
            "required_scenario_evidence_fields",
        ):
            payload[key] = list(payload[key])
        return payload


def build_live_evidence_packet_specs() -> tuple[LiveGigaChatEvidencePacketSpec, ...]:
    return tuple(
        LiveGigaChatEvidencePacketSpec(
            scenario_id=scenario_id,
            provider=REQUIRED_PROVIDER,
            route=PUBLIC_API_DEV_ROUTE,
            evidence_packet_state=EVIDENCE_PACKET_STATE,
            review_state=INITIAL_REVIEW_STATE,
            required_live_inputs=REQUIRED_LIVE_INPUTS,
            required_packet_components=REQUIRED_EVIDENCE_PACKET_COMPONENTS,
            required_packet_index_fields=REQUIRED_PACKET_INDEX_FIELDS,
            required_scenario_evidence_fields=REQUIRED_SCENARIO_EVIDENCE_FIELDS,
            accepted_future_claim_wording=ACCEPTED_FINAL_CLAIM_WORDING,
        )
        for scenario_id in S10_SCENARIO_IDS
    )


LIVE_EVIDENCE_PACKET_SPECS = build_live_evidence_packet_specs()


def validate_live_gigachat_evidence_packet_export_contract() -> list[str]:
    errors: list[str] = []
    s13a = selected_benchmark_review_packet_skeleton_report()
    s13b = live_gigachat_selected_benchmark_report({})
    if s13a.get("status") != "ready":
        errors.append("S13c requires S13a review packet skeleton to be ready")
    if s13a.get("scenario_review_packet_count") != 12:
        errors.append("S13c requires 12 S13a review packet skeletons")
    if s13b.get("status") != "ready":
        errors.append("S13c requires S13b live generation workflow contract to be ready")
    if s13b.get("route_required_by_s13b") != PUBLIC_API_DEV_ROUTE:
        errors.append("S13c requires S13b route public_api_dev")
    if len(LIVE_EVIDENCE_PACKET_SPECS) != 12:
        errors.append(f"S13c must define exactly 12 live evidence packet specs, got {len(LIVE_EVIDENCE_PACKET_SPECS)}")

    by_id = {spec.scenario_id: spec for spec in LIVE_EVIDENCE_PACKET_SPECS}
    for scenario_id in S10_SCENARIO_IDS:
        spec = by_id.get(scenario_id)
        if spec is None:
            errors.append(f"missing S13c evidence packet spec: {scenario_id}")
            continue
        if spec.provider != REQUIRED_PROVIDER:
            errors.append(f"{scenario_id}: provider must be GigaChat")
        if spec.route != PUBLIC_API_DEV_ROUTE:
            errors.append(f"{scenario_id}: route must be public_api_dev")
        if spec.evidence_packet_state != EVIDENCE_PACKET_STATE:
            errors.append(f"{scenario_id}: evidence packet state mismatch")
        if spec.review_state != INITIAL_REVIEW_STATE:
            errors.append(f"{scenario_id}: review state must remain pending_human_review")
        for item in REQUIRED_LIVE_INPUTS:
            if item not in spec.required_live_inputs:
                errors.append(f"{scenario_id}: missing live input {item}")
        for component in REQUIRED_EVIDENCE_PACKET_COMPONENTS:
            if component not in spec.required_packet_components:
                errors.append(f"{scenario_id}: missing evidence packet component {component}")
        for field in REQUIRED_SCENARIO_EVIDENCE_FIELDS:
            if field not in spec.required_scenario_evidence_fields:
                errors.append(f"{scenario_id}: missing scenario evidence field {field}")
        for field in REQUIRED_PACKET_INDEX_FIELDS:
            if field not in spec.required_packet_index_fields:
                errors.append(f"{scenario_id}: missing packet index field {field}")
        if spec.accepted_future_claim_wording != ACCEPTED_FINAL_CLAIM_WORDING:
            errors.append(f"{scenario_id}: accepted future claim wording mismatch")
        if not spec.live_generation_must_already_exist:
            errors.append(f"{scenario_id}: S13c must require prior S13b live generation evidence")
        if spec.live_generation_performed_by_s13c:
            errors.append(f"{scenario_id}: S13c must not run live generation again")
        if spec.credential_values_recorded:
            errors.append(f"{scenario_id}: credential values must never be recorded")
        if not spec.response_digest_required:
            errors.append(f"{scenario_id}: response digest is required")
        if spec.completed_human_review_results_present:
            errors.append(f"{scenario_id}: S13c must not include completed human review results")
        if spec.human_review_results_fabricated:
            errors.append(f"{scenario_id}: S13c must not fabricate human review results")
        if spec.auto_approval_allowed:
            errors.append(f"{scenario_id}: auto approval must not be allowed")
        if spec.selected_parity_claim_supported_now:
            errors.append(f"{scenario_id}: evidence packet alone must not support selected parity claim")
        if not spec.public_api_dev_route_is_not_server3_proof:
            errors.append(f"{scenario_id}: public_api_dev must be marked as not Server 3 proof")
        if spec.server3_local_intranet_verified:
            errors.append(f"{scenario_id}: S13c must not claim Server 3 local_intranet verification")
        if spec.kimi_level_claimed:
            errors.append(f"{scenario_id}: S13c must not claim Kimi-level")
    return errors


def live_gigachat_evidence_packet_export_report() -> dict[str, Any]:
    errors = validate_live_gigachat_evidence_packet_export_contract()
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S13C_WORKFLOW_ID,
        "s_phase": S13C_PHASE_ID,
        "live_gigachat_evidence_packet_export_contract_ready_by_s13c": not errors,
        "scenario_evidence_packet_count": len(LIVE_EVIDENCE_PACKET_SPECS),
        "scenario_ids": list(S10_SCENARIO_IDS),
        "provider_recorded_by_s13c": REQUIRED_PROVIDER,
        "route_recorded_by_s13c": PUBLIC_API_DEV_ROUTE,
        "required_live_inputs": list(REQUIRED_LIVE_INPUTS),
        "required_evidence_packet_components": list(REQUIRED_EVIDENCE_PACKET_COMPONENTS),
        "required_scenario_evidence_fields": list(REQUIRED_SCENARIO_EVIDENCE_FIELDS),
        "review_state_after_s13c": INITIAL_REVIEW_STATE,
        "live_generation_performed_by_s13c_static_check": False,
        "requires_prior_s13b_live_generation_by_s13c": True,
        "credential_values_recorded_by_s13c": False,
        "raw_secret_values_recorded_by_s13c": False,
        "response_digest_required_by_s13c": True,
        "completed_human_review_results_present_by_s13c": False,
        "human_review_results_fabricated_by_s13c": False,
        "auto_approval_allowed_by_s13c": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13c": False,
        "selected_offline_workflow_parity_claim_requires_future_completed_results_by_s13c": True,
        "accepted_future_claim_wording_by_s13c": ACCEPTED_FINAL_CLAIM_WORDING,
        "server3_local_intranet_route_verified_by_s13c": False,
        "public_api_dev_route_is_not_server3_proof_by_s13c": True,
        "hidden_public_internet_allowed_by_s13c": False,
        "cloud_research_allowed_by_s13c": False,
        "cloud_vision_allowed_by_s13c": False,
        "kimi_level_claimed_by_s13c": False,
        "whole_project_kimi_level_supported": False,
        "api_endpoint_added_by_s13c": False,
        "db_schema_migration_added_by_s13c": False,
        "frontend_runtime_changed_by_s13c": False,
        "dependency_versions_changed_by_s13c": False,
        "dockerfiles_changed_by_s13c": False,
        "next_recommended_step": "Run the S13c evidence packet export command against the S13b live artifacts ZIP, then perform real human review; do not claim selected parity until completed review results are ingested.",
        "contract": {
            "forbidden_actions": list(FORBIDDEN_S13C_ACTIONS),
            "live_evidence_packet_specs": [spec.as_dict() for spec in LIVE_EVIDENCE_PACKET_SPECS],
        },
        "errors": errors,
    }
