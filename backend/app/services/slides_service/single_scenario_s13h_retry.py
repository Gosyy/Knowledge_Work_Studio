from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.live_gigachat_selected_benchmark import PUBLIC_API_DEV_ROUTE, REQUIRED_PROVIDER
from backend.app.services.slides_service.targeted_s13g_retry import targeted_s13g_retry_report

S13I_WORKFLOW_ID = "slides.single_scenario_executive_memo_retry"
S13I_PHASE_ID = "S13i"
S13I_RETRY_SCENARIO_ID = "executive_memo_to_board_deck"
S13I_EXPECTED_PRIOR_CANONICAL_VALID_COUNT = 11
S13I_EXPECTED_FINAL_CANONICAL_VALID_COUNT = 12

REUSED_S13H_OUTPUT_REQUIREMENTS = (
    "prior_s13h_merged_canonical_outputs_zip",
    "prior_s13h_canonical_valid_outputs_count_11",
    "prior_s13h_browser_evidence_retry_success",
    "adapter_provenance_preserved",
)

SINGLE_RETRY_OUTPUT_REQUIREMENTS = (
    "single_scenario_model_response_json",
    "single_scenario_canonical_payload_json",
    "single_scenario_canonical_payload_digest",
    "retry_reason_s13h_json_parse_failed",
    "retry_attempt_count",
    "adapter_provenance_present",
)

MERGED_OUTPUT_REQUIREMENTS = (
    "s13i_single_scenario_retry_manifest_json",
    "merged_12_scenario_canonical_outputs_zip",
    "canonical_schema_valid_scenario_count_after_merge_12",
    "review_state_pending",
)

FORBIDDEN_S13I_ACTIONS = (
    "retry_all_scenarios",
    "retry_browser_evidence_again_after_s13h_success",
    "discard_canonical_valid_s13h_outputs",
    "treat_adapter_fields_as_model_generated",
    "fabricate_human_review_results",
    "auto_approve_scenarios",
    "claim_selected_offline_workflow_parity",
    "claim_kimi_level_achieved",
    "claim_server3_local_intranet_verified",
    "record_raw_credentials",
)


@dataclass(frozen=True)
class SingleScenarioRetryPolicy:
    scenario_id: str
    route: str
    provider: str
    retry_required: bool
    reuse_prior_s13h_output: bool
    retry_reason: str
    completed_human_review_results_present: bool = False
    selected_parity_claim_supported_now: bool = False
    server3_local_intranet_verified: bool = False
    kimi_level_claimed: bool = False
    credential_values_recorded: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_single_scenario_retry_policies() -> tuple[SingleScenarioRetryPolicy, ...]:
    policies: list[SingleScenarioRetryPolicy] = []
    for scenario_id in S10_SCENARIO_IDS:
        retry_required = scenario_id == S13I_RETRY_SCENARIO_ID
        policies.append(
            SingleScenarioRetryPolicy(
                scenario_id=scenario_id,
                route=PUBLIC_API_DEV_ROUTE,
                provider=REQUIRED_PROVIDER,
                retry_required=retry_required,
                reuse_prior_s13h_output=not retry_required,
                retry_reason="s13h_executive_memo_json_parse_failed" if retry_required else "canonical_valid_in_prior_s13h",
            )
        )
    return tuple(policies)


S13I_SINGLE_RETRY_POLICIES = build_single_scenario_retry_policies()


def validate_single_scenario_retry_contract() -> list[str]:
    errors: list[str] = []
    s13h = targeted_s13g_retry_report()
    if s13h.get("status") != "ready":
        errors.append("S13i requires S13h targeted retry contract to be ready")
    if len(S13I_SINGLE_RETRY_POLICIES) != len(S10_SCENARIO_IDS):
        errors.append("S13i must cover all 12 selected benchmark scenarios")
    if S13I_RETRY_SCENARIO_ID not in S10_SCENARIO_IDS:
        errors.append("S13i retry scenario must be one of the S10 scenarios")

    retry_policies = [policy for policy in S13I_SINGLE_RETRY_POLICIES if policy.retry_required]
    reused_policies = [policy for policy in S13I_SINGLE_RETRY_POLICIES if policy.reuse_prior_s13h_output]
    if [policy.scenario_id for policy in retry_policies] != [S13I_RETRY_SCENARIO_ID]:
        errors.append("S13i must retry only executive_memo_to_board_deck")
    if len(reused_policies) != 11:
        errors.append("S13i must reuse 11 prior S13h canonical-valid outputs")

    for policy in S13I_SINGLE_RETRY_POLICIES:
        if policy.route != PUBLIC_API_DEV_ROUTE or policy.provider != REQUIRED_PROVIDER:
            errors.append(f"{policy.scenario_id}: route/provider mismatch")
        should_retry = policy.scenario_id == S13I_RETRY_SCENARIO_ID
        if policy.retry_required is not should_retry:
            errors.append(f"{policy.scenario_id}: retry_required mismatch")
        if policy.reuse_prior_s13h_output is not (not should_retry):
            errors.append(f"{policy.scenario_id}: reuse_prior_s13h_output mismatch")
        if should_retry and policy.retry_reason != "s13h_executive_memo_json_parse_failed":
            errors.append(f"{policy.scenario_id}: retry reason mismatch")
        for name, value in {
            "completed_human_review_results_present": policy.completed_human_review_results_present,
            "selected_parity_claim_supported_now": policy.selected_parity_claim_supported_now,
            "server3_local_intranet_verified": policy.server3_local_intranet_verified,
            "kimi_level_claimed": policy.kimi_level_claimed,
            "credential_values_recorded": policy.credential_values_recorded,
        }.items():
            if value is not False:
                errors.append(f"{policy.scenario_id}: {name} must be false")
    return errors


def single_scenario_executive_memo_retry_report() -> dict[str, Any]:
    errors = validate_single_scenario_retry_contract()
    retry_policies = [policy for policy in S13I_SINGLE_RETRY_POLICIES if policy.retry_required]
    reused_policies = [policy for policy in S13I_SINGLE_RETRY_POLICIES if policy.reuse_prior_s13h_output]
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S13I_WORKFLOW_ID,
        "s_phase": S13I_PHASE_ID,
        "single_scenario_executive_memo_retry_ready_by_s13i": not errors,
        "scenario_count": len(S13I_SINGLE_RETRY_POLICIES),
        "retry_scenario_count": len(retry_policies),
        "reused_canonical_scenario_count": len(reused_policies),
        "retry_scenario_ids": [policy.scenario_id for policy in retry_policies],
        "reused_scenario_ids": [policy.scenario_id for policy in reused_policies],
        "expected_prior_canonical_valid_count_by_s13i": S13I_EXPECTED_PRIOR_CANONICAL_VALID_COUNT,
        "expected_final_canonical_valid_count_by_s13i": S13I_EXPECTED_FINAL_CANONICAL_VALID_COUNT,
        "route_required_by_s13i": PUBLIC_API_DEV_ROUTE,
        "provider_required_by_s13i": REQUIRED_PROVIDER,
        "requires_prior_s13h_live_zip_by_s13i": True,
        "requires_shell_env_credentials_for_retry_by_s13i": True,
        "static_check_calls_gigachat_by_s13i": False,
        "reuses_prior_s13h_canonical_valid_outputs_by_s13i": True,
        "single_scenario_retry_only_by_s13i": True,
        "adapter_provenance_required_by_s13i": True,
        "model_vs_adapter_field_separation_required_by_s13i": True,
        "completed_human_review_results_present_by_s13i": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13i": False,
        "server3_local_intranet_route_verified_by_s13i": False,
        "public_api_dev_route_is_not_server3_proof_by_s13i": True,
        "credential_values_recorded_by_s13i": False,
        "kimi_level_claimed_by_s13i": False,
        "whole_project_kimi_level_supported": False,
        "api_endpoint_added_by_s13i": False,
        "db_schema_migration_added_by_s13i": False,
        "frontend_runtime_changed_by_s13i": False,
        "dependency_versions_changed_by_s13i": False,
        "dockerfiles_changed_by_s13i": False,
        "reused_s13h_output_requirements": list(REUSED_S13H_OUTPUT_REQUIREMENTS),
        "single_retry_output_requirements": list(SINGLE_RETRY_OUTPUT_REQUIREMENTS),
        "merged_output_requirements": list(MERGED_OUTPUT_REQUIREMENTS),
        "forbidden_actions": list(FORBIDDEN_S13I_ACTIONS),
        "next_recommended_step": "Run S13i single-scenario live retry against the prior S13h 11/12 ZIP; export a review packet only if the merged result is 12/12 canonical-valid.",
        "contract": {
            "policies": [policy.as_dict() for policy in S13I_SINGLE_RETRY_POLICIES],
        },
        "errors": errors,
    }
