from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.live_benchmark_prompt_schema_hardening import (
    MIN_REQUIRED_SLIDES_PER_SCENARIO,
    REQUIRED_RENDER_QA_CHECKS,
    REQUIRED_RESPONSE_SCHEMA_FIELDS,
    REQUIRED_SLIDE_FIELDS,
    live_benchmark_prompt_schema_hardening_report,
)
from backend.app.services.slides_service.hardened_output_repair import hardened_output_repair_report
from backend.app.services.slides_service.live_gigachat_selected_benchmark import PUBLIC_API_DEV_ROUTE, REQUIRED_PROVIDER

S13F_WORKFLOW_ID = "slides.strict_json_per_scenario_rerun"
S13F_PHASE_ID = "S13f"
STRICT_SCHEMA_ECHO_FIELDS = (
    "schema_name",
    "schema_version",
    "scenario_id",
    "required_top_level_fields",
    "required_slide_fields",
    "minimum_slide_count",
    "required_render_qa_checks",
)
STRICT_RESPONSE_SCHEMA_FIELDS = REQUIRED_RESPONSE_SCHEMA_FIELDS + ("schema_echo", "validation_targets")
VALIDATION_TARGET_FIELDS = (
    "strict_json_object_only",
    "schema_echo_matches_prompt",
    "minimum_slide_count_met",
    "every_slide_has_purpose",
    "every_slide_has_citation_requirements",
    "every_slide_has_render_qa_checks",
    "safety_boundaries_all_false",
)
REPAIR_FALLBACK_ACTIONS = (
    "strip_markdown_code_fences",
    "json_raw_decode_first_object",
    "trim_trailing_extra_data",
    "sanitize_invalid_json_control_characters",
)
FORBIDDEN_S13F_ACTIONS = (
    "accept_missing_slide_purpose",
    "fabricate_human_review_results",
    "auto_approve_scenarios",
    "claim_selected_offline_workflow_parity",
    "claim_kimi_level_achieved",
    "claim_server3_local_intranet_verified",
    "record_raw_credentials",
)


@dataclass(frozen=True)
class StrictJsonRerunScenarioPolicy:
    scenario_id: str
    route: str
    provider: str
    minimum_slide_count: int
    strict_json_only: bool = True
    per_scenario_fail_fast: bool = True
    schema_echo_required: bool = True
    repair_fallback_allowed: bool = True
    static_check_calls_gigachat: bool = False
    completed_human_review_results_present: bool = False
    selected_parity_claim_supported_now: bool = False
    server3_local_intranet_verified: bool = False
    kimi_level_claimed: bool = False
    credential_values_recorded: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


STRICT_JSON_RERUN_POLICIES = tuple(
    StrictJsonRerunScenarioPolicy(
        scenario_id=scenario_id,
        route=PUBLIC_API_DEV_ROUTE,
        provider=REQUIRED_PROVIDER,
        minimum_slide_count=MIN_REQUIRED_SLIDES_PER_SCENARIO,
    )
    for scenario_id in S10_SCENARIO_IDS
)


def strict_schema_echo_for_scenario(scenario_id: str) -> dict[str, Any]:
    return {
        "schema_name": "kw_s13f_strict_selected_benchmark_plan",
        "schema_version": "s13f.strict_json.v1",
        "scenario_id": scenario_id,
        "required_top_level_fields": list(STRICT_RESPONSE_SCHEMA_FIELDS),
        "required_slide_fields": list(REQUIRED_SLIDE_FIELDS),
        "minimum_slide_count": MIN_REQUIRED_SLIDES_PER_SCENARIO,
        "required_render_qa_checks": list(REQUIRED_RENDER_QA_CHECKS),
    }


def build_minimal_valid_s13f_payload(scenario_id: str) -> dict[str, Any]:
    slides = []
    for index in range(1, MIN_REQUIRED_SLIDES_PER_SCENARIO + 1):
        slides.append(
            {
                "slide_id": f"s{index:02d}",
                "title": f"{scenario_id} slide {index}",
                "purpose": f"Scenario-specific purpose for {scenario_id} slide {index}",
                "source_grounding_required": True,
                "native_visuals": ["pptx_table"],
                "citation_requirements": ["claim_to_source_fragment_mapping_required"],
                "render_qa_checks": list(REQUIRED_RENDER_QA_CHECKS[:5]),
            }
        )
    return {
        "schema_echo": strict_schema_echo_for_scenario(scenario_id),
        "scenario_id": scenario_id,
        "title": f"Strict S13f plan for {scenario_id}",
        "scenario_summary": f"Scenario-specific benchmark plan for {scenario_id}.",
        "approved_plan_candidate": {
            "storyline": ["context", "source-backed analysis", "decision arc", "operator next actions"],
            "assumptions_to_verify": ["all claims require source fragments"],
            "non_goals": ["no approval", "no Kimi-level claim", "no Server 3 proof"],
        },
        "slide_outline": slides,
        "native_visuals": [
            {
                "visual_id": "v01",
                "visual_type": "pptx_table",
                "editable_pptx_native": True,
                "source_fields_required": ["source_id", "fragment_id", "claim_id"],
                "render_qa_checks": list(REQUIRED_RENDER_QA_CHECKS),
            }
        ],
        "citation_obligations": {"slide_level_claims_require_sources": True, "minimum_citation_coverage": 1.0},
        "render_qa_obligations": {"actual_slide_render_required": True, "geometry_manifest_required": True, "checks": list(REQUIRED_RENDER_QA_CHECKS)},
        "evidence_manifest": {"required_outputs": [], "required_s_phase_evidence": []},
        "human_review_handoff": {"review_state": "pending_human_review", "allowed_decisions": ["approve", "request_rework", "reject"], "do_not_auto_fill": True},
        "safety_boundaries": {
            "selected_parity_claim_supported_now": False,
            "kimi_level_claimed": False,
            "server3_local_intranet_verified": False,
            "completed_human_review_results_present": False,
            "credential_values_recorded": False,
        },
        "validation_targets": {field: True for field in VALIDATION_TARGET_FIELDS},
    }


def strict_json_prompt_for_scenario(scenario_id: str) -> str:
    if scenario_id not in S10_SCENARIO_IDS:
        raise ValueError(f"unknown S10 scenario: {scenario_id}")
    return (
        "Return exactly one JSON object and nothing else. Do not use markdown fences. Do not include trailing commentary. "
        f"Scenario id: {scenario_id}. Route: public_api_dev. Provider: GigaChat. "
        f"Include at least {MIN_REQUIRED_SLIDES_PER_SCENARIO} slide_outline entries. Every slide must include a non-empty purpose. "
        "Echo schema_echo exactly and keep all safety boundaries false. JSON contract: "
        + json.dumps(build_minimal_valid_s13f_payload(scenario_id), ensure_ascii=False, sort_keys=True)
    )


def validate_strict_s13f_payload(payload: Any, scenario_id: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["response must be a JSON object"]
    for field in STRICT_RESPONSE_SCHEMA_FIELDS:
        if field not in payload:
            errors.append(f"missing response field: {field}")
    if payload.get("scenario_id") != scenario_id:
        errors.append("scenario_id mismatch")
    if payload.get("schema_echo") != strict_schema_echo_for_scenario(scenario_id):
        errors.append("schema_echo mismatch")
    slides = payload.get("slide_outline")
    if not isinstance(slides, list) or len(slides) < MIN_REQUIRED_SLIDES_PER_SCENARIO:
        errors.append(f"slide_outline must contain at least {MIN_REQUIRED_SLIDES_PER_SCENARIO} slides")
    else:
        for index, slide in enumerate(slides, start=1):
            if not isinstance(slide, dict):
                errors.append(f"slide {index} must be an object")
                continue
            for field in REQUIRED_SLIDE_FIELDS:
                if field not in slide:
                    errors.append(f"slide {index} missing field: {field}")
            if not str(slide.get("purpose") or "").strip():
                errors.append(f"slide {index} purpose must be non-empty")
            if slide.get("source_grounding_required") is not True:
                errors.append(f"slide {index} source_grounding_required must be true")
    targets = payload.get("validation_targets")
    if not isinstance(targets, dict):
        errors.append("validation_targets must be an object")
    else:
        for field in VALIDATION_TARGET_FIELDS:
            if targets.get(field) is not True:
                errors.append(f"validation_targets.{field} must be true")
    safety = payload.get("safety_boundaries")
    if not isinstance(safety, dict):
        errors.append("safety_boundaries must be an object")
    else:
        for field in (
            "selected_parity_claim_supported_now",
            "kimi_level_claimed",
            "server3_local_intranet_verified",
            "completed_human_review_results_present",
            "credential_values_recorded",
        ):
            if safety.get(field) is not False:
                errors.append(f"safety_boundaries.{field} must be false")
    return errors


def validate_strict_json_rerun_contract() -> list[str]:
    errors: list[str] = []
    if live_benchmark_prompt_schema_hardening_report().get("status") != "ready":
        errors.append("S13f requires S13d prompt/schema hardening contract to be ready")
    if hardened_output_repair_report().get("status") != "ready":
        errors.append("S13f requires S13e output repair contract to be ready")
    if len(STRICT_JSON_RERUN_POLICIES) != 12:
        errors.append("S13f must cover 12 selected benchmark scenarios")
    sample_errors = validate_strict_s13f_payload(build_minimal_valid_s13f_payload(S10_SCENARIO_IDS[0]), S10_SCENARIO_IDS[0])
    if sample_errors:
        errors.append(f"S13f sample valid payload failed validation: {sample_errors[:3]}")
    return errors


def strict_json_per_scenario_rerun_report() -> dict[str, Any]:
    errors = validate_strict_json_rerun_contract()
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S13F_WORKFLOW_ID,
        "s_phase": S13F_PHASE_ID,
        "strict_per_scenario_json_rerun_ready_by_s13f": not errors,
        "scenario_count": len(STRICT_JSON_RERUN_POLICIES),
        "route_required_by_s13f": PUBLIC_API_DEV_ROUTE,
        "provider_required_by_s13f": REQUIRED_PROVIDER,
        "strict_json_only_by_s13f": True,
        "schema_echo_required_by_s13f": True,
        "per_scenario_fail_fast_by_s13f": True,
        "repair_fallback_allowed_by_s13f": True,
        "minimum_slide_count_per_scenario_by_s13f": MIN_REQUIRED_SLIDES_PER_SCENARIO,
        "static_check_calls_gigachat_by_s13f": False,
        "completed_human_review_results_present_by_s13f": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13f": False,
        "server3_local_intranet_route_verified_by_s13f": False,
        "public_api_dev_route_is_not_server3_proof_by_s13f": True,
        "credential_values_recorded_by_s13f": False,
        "kimi_level_claimed_by_s13f": False,
        "whole_project_kimi_level_supported": False,
        "api_endpoint_added_by_s13f": False,
        "db_schema_migration_added_by_s13f": False,
        "frontend_runtime_changed_by_s13f": False,
        "dependency_versions_changed_by_s13f": False,
        "dockerfiles_changed_by_s13f": False,
        "next_recommended_step": "Run S13f strict per-scenario live rerun with shell env GigaChat credentials; export accepted strict outputs only if 12/12 schema-valid.",
        "contract": {
            "strict_json_rerun_policies": [policy.as_dict() for policy in STRICT_JSON_RERUN_POLICIES],
            "forbidden_actions": list(FORBIDDEN_S13F_ACTIONS),
            "repair_fallback_actions": list(REPAIR_FALLBACK_ACTIONS),
        },
        "errors": errors,
    }
