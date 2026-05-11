from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.canonical_schema_adapter import (
    canonical_schema_adapter_report,
)
from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.live_gigachat_selected_benchmark import (
    PUBLIC_API_DEV_ROUTE,
    REQUIRED_PROVIDER,
)

S13H_WORKFLOW_ID = "slides.targeted_retry_failed_s13g_scenarios"
S13H_PHASE_ID = "S13h"

KNOWN_FAILED_S13G_SCENARIOS = (
    "executive_memo_to_board_deck",
    "browser_evidence_packet_to_cited_deck",
)

REUSED_CANONICAL_OUTPUT_REQUIREMENTS = (
    "prior_s13g_canonical_payload",
    "prior_s13g_canonical_payload_digest",
    "prior_s13g_model_payload_digest",
    "adapter_provenance_preserved",
)

RETRY_OUTPUT_REQUIREMENTS = (
    "targeted_retry_model_response_json",
    "targeted_retry_canonical_payload_json",
    "targeted_retry_canonical_payload_digest",
    "retry_reason",
    "retry_attempt_count",
    "adapter_provenance_present",
)

COMBINED_OUTPUT_REQUIREMENTS = (
    "s13h_targeted_retry_manifest_json",
    "combined_scenario_canonical_payloads_json",
    "combined_canonical_output_zip",
    "review_state_pending",
)

FORBIDDEN_S13H_ACTIONS = (
    "retry_all_scenarios_when_only_targeted_failures_exist",
    "discard_canonical_valid_s13g_outputs",
    "treat_adapter_fields_as_model_generated",
    "fabricate_human_review_results",
    "auto_approve_scenarios",
    "claim_selected_offline_workflow_parity",
    "claim_kimi_level_achieved",
    "claim_server3_local_intranet_verified",
    "record_raw_credentials",
)


@dataclass(frozen=True)
class TargetedRetryScenarioPolicy:
    scenario_id: str
    route: str
    provider: str
    retry_required: bool
    reuse_prior_canonical_output: bool
    retry_reason: str
    completed_human_review_results_present: bool = False
    selected_parity_claim_supported_now: bool = False
    server3_local_intranet_verified: bool = False
    kimi_level_claimed: bool = False
    credential_values_recorded: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_targeted_retry_policies() -> tuple[TargetedRetryScenarioPolicy, ...]:
    policies: list[TargetedRetryScenarioPolicy] = []
    failed = set(KNOWN_FAILED_S13G_SCENARIOS)
    for scenario_id in S10_SCENARIO_IDS:
        retry_required = scenario_id in failed
        policies.append(
            TargetedRetryScenarioPolicy(
                scenario_id=scenario_id,
                route=PUBLIC_API_DEV_ROUTE,
                provider=REQUIRED_PROVIDER,
                retry_required=retry_required,
                reuse_prior_canonical_output=not retry_required,
                retry_reason="s13g_json_parse_failed" if retry_required else "canonical_valid_in_prior_s13g",
            )
        )
    return tuple(policies)


S13H_TARGETED_RETRY_POLICIES = build_targeted_retry_policies()


def validate_targeted_s13g_retry_contract() -> list[str]:
    errors: list[str] = []
    s13g = canonical_schema_adapter_report()
    if s13g.get("status") != "ready":
        errors.append("S13h requires S13g canonical schema adapter contract to be ready")
    if len(S13H_TARGETED_RETRY_POLICIES) != len(S10_SCENARIO_IDS):
        errors.append("S13h must cover all 12 selected benchmark scenarios")
    failed = set(KNOWN_FAILED_S13G_SCENARIOS)
    if failed != {"executive_memo_to_board_deck", "browser_evidence_packet_to_cited_deck"}:
        errors.append("S13h known failed scenario set is unexpected")

    for scenario_id in KNOWN_FAILED_S13G_SCENARIOS:
        if scenario_id not in S10_SCENARIO_IDS:
            errors.append(f"unknown S13h retry scenario: {scenario_id}")

    for policy in S13H_TARGETED_RETRY_POLICIES:
        if policy.route != PUBLIC_API_DEV_ROUTE or policy.provider != REQUIRED_PROVIDER:
            errors.append(f"{policy.scenario_id}: route/provider mismatch")
        should_retry = policy.scenario_id in failed
        if policy.retry_required is not should_retry:
            errors.append(f"{policy.scenario_id}: retry_required mismatch")
        if policy.reuse_prior_canonical_output is not (not should_retry):
            errors.append(f"{policy.scenario_id}: reuse_prior_canonical_output mismatch")
        if should_retry and not policy.retry_reason:
            errors.append(f"{policy.scenario_id}: retry reason required")
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


def targeted_s13g_retry_report() -> dict[str, Any]:
    errors = validate_targeted_s13g_retry_contract()
    retry_policies = [policy for policy in S13H_TARGETED_RETRY_POLICIES if policy.retry_required]
    reused_policies = [policy for policy in S13H_TARGETED_RETRY_POLICIES if policy.reuse_prior_canonical_output]
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S13H_WORKFLOW_ID,
        "s_phase": S13H_PHASE_ID,
        "targeted_retry_failed_s13g_scenarios_ready_by_s13h": not errors,
        "scenario_count": len(S13H_TARGETED_RETRY_POLICIES),
        "retry_scenario_count": len(retry_policies),
        "reused_canonical_scenario_count": len(reused_policies),
        "retry_scenario_ids": [policy.scenario_id for policy in retry_policies],
        "reused_scenario_ids": [policy.scenario_id for policy in reused_policies],
        "route_required_by_s13h": PUBLIC_API_DEV_ROUTE,
        "provider_required_by_s13h": REQUIRED_PROVIDER,
        "requires_prior_s13g_live_zip_by_s13h": True,
        "requires_shell_env_credentials_for_retry_by_s13h": True,
        "static_check_calls_gigachat_by_s13h": False,
        "reuses_prior_canonical_valid_outputs_by_s13h": True,
        "targeted_retry_only_by_s13h": True,
        "adapter_provenance_required_by_s13h": True,
        "model_vs_adapter_field_separation_required_by_s13h": True,
        "completed_human_review_results_present_by_s13h": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13h": False,
        "server3_local_intranet_route_verified_by_s13h": False,
        "public_api_dev_route_is_not_server3_proof_by_s13h": True,
        "credential_values_recorded_by_s13h": False,
        "kimi_level_claimed_by_s13h": False,
        "whole_project_kimi_level_supported": False,
        "api_endpoint_added_by_s13h": False,
        "db_schema_migration_added_by_s13h": False,
        "frontend_runtime_changed_by_s13h": False,
        "dependency_versions_changed_by_s13h": False,
        "dockerfiles_changed_by_s13h": False,
        "reused_canonical_output_requirements": list(REUSED_CANONICAL_OUTPUT_REQUIREMENTS),
        "retry_output_requirements": list(RETRY_OUTPUT_REQUIREMENTS),
        "combined_output_requirements": list(COMBINED_OUTPUT_REQUIREMENTS),
        "forbidden_actions": list(FORBIDDEN_S13H_ACTIONS),
        "next_recommended_step": "Run S13h targeted live retry against the failed S13g scenarios only; export a review packet only if the merged result is 12/12 canonical-valid.",
        "contract": {
            "policies": [policy.as_dict() for policy in S13H_TARGETED_RETRY_POLICIES],
        },
        "errors": errors,
    }
