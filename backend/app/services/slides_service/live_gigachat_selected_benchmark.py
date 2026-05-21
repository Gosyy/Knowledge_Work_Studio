from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.kimi_style_benchmark import (
    ACCEPTED_FINAL_CLAIM_WORDING,
    REQUIRED_AUTOMATED_EVIDENCE,
    S10_SCENARIO_IDS,
)
from backend.app.services.slides_service.selected_benchmark_review_packet import (
    selected_benchmark_review_packet_skeleton_report,
)

S13B_WORKFLOW_ID = "slides.live_public_api_dev_gigachat_generation"
S13B_PHASE_ID = "S13b"
PUBLIC_API_DEV_ROUTE = "public_api_dev"
REQUIRED_PROVIDER = "GigaChat"
LIVE_GENERATION_STATE = "awaiting_live_public_api_dev_generation"
POST_LIVE_GENERATION_STATE = "generated_artifacts_ready"

SECRET_ENV_NAMES = (
    "KW_RC3_GIGACHAT_AUTHORIZATION_KEY",
    "KW_RC3_GIGACHAT_AUTH_KEY",
    "GIGACHAT_CREDENTIALS",
    "KW_RC3_GIGACHAT_CLIENT_ID",
    "KW_RC3_GIGACHAT_CLIENT_SECRET",
    "KW_RC3_GIGACHAT_ACCESS_TOKEN",
    "KW_RC3_GIGACHAT_BEARER",
    "GIGACHAT_ACCESS_TOKEN",
)

REQUIRED_LIVE_OUTPUTS = (
    "scenario_generation_manifest_json",
    "scenario_model_response_json",
    "approved_plan_candidate_json",
    "artifact_generation_request_json",
    "safe_metadata_json",
    "citation_manifest_placeholder_json",
    "render_qa_input_placeholder_json",
)

REQUIRED_SAFETY_CONTROLS = (
    "credentials_from_shell_env_only",
    "credential_values_never_recorded",
    "public_api_dev_route_explicitly_recorded",
    "server3_local_intranet_not_claimed",
    "no_auto_human_review_completion",
    "no_selected_parity_claim",
    "no_generic_kimi_level_claim",
)

FORBIDDEN_S13B_ACTIONS = (
    "commit_gigachat_credentials",
    "record_raw_access_token",
    "claim_server3_local_intranet_verified",
    "claim_selected_parity_from_generation_only",
    "claim_kimi_level_achieved",
    "complete_human_review_automatically",
    "auto_approve_scenarios",
)


@dataclass(frozen=True)
class LiveGigaChatScenarioExecutionSpec:
    scenario_id: str
    provider: str
    route: str
    initial_execution_state: str
    post_live_execution_state: str
    required_outputs: tuple[str, ...]
    required_safety_controls: tuple[str, ...]
    expected_automated_evidence: tuple[str, ...]
    credential_values_recorded: bool = False
    public_api_dev_generation_required: bool = True
    production_server3_local_intranet_verified: bool = False
    completed_human_review_results_present: bool = False
    selected_parity_claim_supported_now: bool = False
    kimi_level_claimed: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("required_outputs", "required_safety_controls", "expected_automated_evidence"):
            payload[key] = list(payload[key])
        return payload


def build_live_scenario_specs() -> tuple[LiveGigaChatScenarioExecutionSpec, ...]:
    return tuple(
        LiveGigaChatScenarioExecutionSpec(
            scenario_id=scenario_id,
            provider=REQUIRED_PROVIDER,
            route=PUBLIC_API_DEV_ROUTE,
            initial_execution_state=LIVE_GENERATION_STATE,
            post_live_execution_state=POST_LIVE_GENERATION_STATE,
            required_outputs=REQUIRED_LIVE_OUTPUTS,
            required_safety_controls=REQUIRED_SAFETY_CONTROLS,
            expected_automated_evidence=REQUIRED_AUTOMATED_EVIDENCE,
        )
        for scenario_id in S10_SCENARIO_IDS
    )


LIVE_SCENARIO_SPECS = build_live_scenario_specs()


def configured_credential_inputs(env: dict[str, str] | None = None) -> tuple[str, ...]:
    source = env or {}
    return tuple(name for name in SECRET_ENV_NAMES if source.get(name, "").strip())


def validate_live_gigachat_selected_benchmark_contract() -> list[str]:
    errors: list[str] = []
    s13a = selected_benchmark_review_packet_skeleton_report()
    if s13a.get("status") != "ready":
        errors.append("S13b requires S13a review packet skeleton to be ready")
    if s13a.get("scenario_review_packet_count") != 12:
        errors.append("S13b requires 12 S13a scenario review packets")
    if s13a.get("public_api_dev_execution_performed_by_s13a") is not False:
        errors.append("S13a must not have performed public_api_dev execution")
    if s13a.get("completed_human_review_results_present_by_s13a") is not False:
        errors.append("S13b must start before completed human review results are present")
    if len(LIVE_SCENARIO_SPECS) != 12:
        errors.append(f"S13b must prepare exactly 12 live scenario specs, got {len(LIVE_SCENARIO_SPECS)}")

    by_id = {spec.scenario_id: spec for spec in LIVE_SCENARIO_SPECS}
    for scenario_id in S10_SCENARIO_IDS:
        spec = by_id.get(scenario_id)
        if spec is None:
            errors.append(f"missing S13b live scenario spec: {scenario_id}")
            continue
        if spec.provider != REQUIRED_PROVIDER:
            errors.append(f"{scenario_id}: provider must be GigaChat")
        if spec.route != PUBLIC_API_DEV_ROUTE:
            errors.append(f"{scenario_id}: route must be public_api_dev")
        if spec.initial_execution_state != LIVE_GENERATION_STATE:
            errors.append(f"{scenario_id}: initial execution state mismatch")
        if spec.post_live_execution_state != POST_LIVE_GENERATION_STATE:
            errors.append(f"{scenario_id}: post-live execution state mismatch")
        for output in REQUIRED_LIVE_OUTPUTS:
            if output not in spec.required_outputs:
                errors.append(f"{scenario_id}: missing live output {output}")
        for control in REQUIRED_SAFETY_CONTROLS:
            if control not in spec.required_safety_controls:
                errors.append(f"{scenario_id}: missing safety control {control}")
        for evidence in REQUIRED_AUTOMATED_EVIDENCE:
            if evidence not in spec.expected_automated_evidence:
                errors.append(f"{scenario_id}: missing automated evidence expectation {evidence}")
        if not spec.public_api_dev_generation_required:
            errors.append(f"{scenario_id}: public_api_dev generation must be required")
        if spec.credential_values_recorded:
            errors.append(f"{scenario_id}: raw credential values must never be recorded")
        if spec.production_server3_local_intranet_verified:
            errors.append(f"{scenario_id}: S13b must not verify Server 3 local_intranet route")
        if spec.completed_human_review_results_present:
            errors.append(f"{scenario_id}: S13b must not include completed human review results")
        if spec.selected_parity_claim_supported_now:
            errors.append(f"{scenario_id}: generation alone must not support selected parity claim")
        if spec.kimi_level_claimed:
            errors.append(f"{scenario_id}: S13b must not claim Kimi-level")
    return errors


def live_gigachat_selected_benchmark_report(env: dict[str, str] | None = None) -> dict[str, Any]:
    errors = validate_live_gigachat_selected_benchmark_contract()
    credential_inputs = configured_credential_inputs(env or {})
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S13B_WORKFLOW_ID,
        "s_phase": S13B_PHASE_ID,
        "live_public_api_dev_gigachat_generation_contract_ready_by_s13b": not errors,
        "scenario_live_generation_spec_count": len(LIVE_SCENARIO_SPECS),
        "scenario_ids": list(S10_SCENARIO_IDS),
        "provider_required_by_s13b": REQUIRED_PROVIDER,
        "route_required_by_s13b": PUBLIC_API_DEV_ROUTE,
        "public_api_dev_generation_required_by_s13b": True,
        "public_api_dev_execution_performed_by_s13b_static_check": False,
        "requires_shell_env_credentials_by_s13b": True,
        "credential_input_names_allowed_by_s13b": list(SECRET_ENV_NAMES),
        "credential_inputs_configured_count": len(credential_inputs),
        "credential_input_names_configured": list(credential_inputs),
        "credential_values_recorded_by_s13b": False,
        "required_live_outputs": list(REQUIRED_LIVE_OUTPUTS),
        "required_safety_controls": list(REQUIRED_SAFETY_CONTROLS),
        "forbidden_actions": list(FORBIDDEN_S13B_ACTIONS),
        "completed_human_review_results_present_by_s13b": False,
        "human_review_results_fabricated_by_s13b": False,
        "auto_approval_allowed_by_s13b": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13b": False,
        "selected_offline_workflow_parity_claim_requires_future_completed_results_by_s13b": True,
        "accepted_future_claim_wording_by_s13b": ACCEPTED_FINAL_CLAIM_WORDING,
        "server3_local_intranet_route_verified_by_s13b": False,
        "public_api_dev_route_is_not_server3_proof_by_s13b": True,
        "hidden_public_internet_allowed_by_s13b": False,
        "public_internet_used_by_s13b_static_check": False,
        "public_internet_required_for_live_s13b": True,
        "cloud_research_allowed_by_s13b": False,
        "cloud_vision_allowed_by_s13b": False,
        "kimi_level_claimed_by_s13b": False,
        "whole_project_kimi_level_supported": False,
        "api_endpoint_added_by_s13b": False,
        "db_schema_migration_added_by_s13b": False,
        "frontend_runtime_changed_by_s13b": False,
        "dependency_versions_changed_by_s13b": False,
        "dockerfiles_changed_by_s13b": False,
        "next_recommended_step": "Run the explicit S13b live public_api_dev generation command with shell env credentials, then export S13c human review packet; do not claim selected parity until completed human review is ingested.",
        "contract": {
            "live_scenario_specs": [spec.as_dict() for spec in LIVE_SCENARIO_SPECS],
        },
        "errors": errors,
    }
