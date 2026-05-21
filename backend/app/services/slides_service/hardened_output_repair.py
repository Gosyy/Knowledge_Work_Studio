from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.live_benchmark_prompt_schema_hardening import (
    REQUIRED_RESPONSE_SCHEMA_FIELDS,
    validate_hardened_response_payload,
    live_benchmark_prompt_schema_hardening_report,
)
from backend.app.services.slides_service.live_gigachat_selected_benchmark import (
    PUBLIC_API_DEV_ROUTE,
    REQUIRED_PROVIDER,
)

S13E_WORKFLOW_ID = "slides.hardened_output_repair_parser"
S13E_PHASE_ID = "S13e"

REPAIR_ACTIONS = (
    "strip_markdown_code_fences",
    "json_raw_decode_first_object",
    "trim_trailing_extra_data",
    "normalize_approved_plan_candidate_nested_schema_fields",
    "sanitize_invalid_json_control_characters",
)

REPAIR_INPUT_REQUIREMENTS = (
    "s13d_hardened_live_generation_manifest_json",
    "s13d_per_scenario_raw_response_json",
    "original_response_digest",
    "scenario_id",
)

REPAIR_OUTPUTS = (
    "repaired_payload_json",
    "repair_manifest_json",
    "schema_validation_report_json",
    "original_response_digest",
    "repaired_payload_digest",
)

FORBIDDEN_S13E_ACTIONS = (
    "call_gigachat_again",
    "change_original_response_digest",
    "fabricate_human_review_results",
    "auto_approve_scenarios",
    "claim_selected_offline_workflow_parity",
    "claim_kimi_level_achieved",
    "claim_server3_local_intranet_verified",
    "record_raw_credentials",
)


@dataclass(frozen=True)
class HardenedOutputRepairResult:
    scenario_id: str
    status: str
    schema_valid: bool
    repair_actions_applied: tuple[str, ...]
    parse_error: str | None
    schema_errors: tuple[str, ...]
    repaired_payload: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["repair_actions_applied"] = list(self.repair_actions_applied)
        payload["schema_errors"] = list(self.schema_errors)
        return payload


@dataclass(frozen=True)
class HardenedOutputRepairContract:
    workflow_id: str
    route: str
    provider: str
    scenario_count: int
    repair_actions: tuple[str, ...]
    input_requirements: tuple[str, ...]
    required_outputs: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    requires_prior_s13d_hardened_live_rerun: bool
    deterministic_repair_only: bool
    live_gigachat_call_allowed_by_s13e: bool
    preserves_original_response_digest: bool
    writes_repair_manifest: bool
    completed_human_review_results_present: bool
    selected_parity_claim_supported_now: bool
    server3_local_intranet_verified: bool
    kimi_level_claimed: bool

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("repair_actions", "input_requirements", "required_outputs", "forbidden_actions"):
            payload[key] = list(payload[key])
        return payload


S13E_REPAIR_CONTRACT = HardenedOutputRepairContract(
    workflow_id=S13E_WORKFLOW_ID,
    route=PUBLIC_API_DEV_ROUTE,
    provider=REQUIRED_PROVIDER,
    scenario_count=len(S10_SCENARIO_IDS),
    repair_actions=REPAIR_ACTIONS,
    input_requirements=REPAIR_INPUT_REQUIREMENTS,
    required_outputs=REPAIR_OUTPUTS,
    forbidden_actions=FORBIDDEN_S13E_ACTIONS,
    requires_prior_s13d_hardened_live_rerun=True,
    deterministic_repair_only=True,
    live_gigachat_call_allowed_by_s13e=False,
    preserves_original_response_digest=True,
    writes_repair_manifest=True,
    completed_human_review_results_present=False,
    selected_parity_claim_supported_now=False,
    server3_local_intranet_verified=False,
    kimi_level_claimed=False,
)


def strip_markdown_code_fences(text: str) -> tuple[str, bool]:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return text, False
    stripped = re.sub(r"^```(?:json|JSON)?\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped, True


def sanitize_invalid_json_control_characters(text: str) -> tuple[str, bool]:
    changed = False
    chars: list[str] = []
    for char in text:
        code = ord(char)
        if code < 32 and char not in "\t\r\n":
            chars.append(" ")
            changed = True
        else:
            chars.append(char)
    return "".join(chars), changed


def decode_first_json_object(text: str) -> tuple[Any, bool, str | None]:
    decoder = json.JSONDecoder()
    stripped = text.strip()
    try:
        payload, end = decoder.raw_decode(stripped)
    except json.JSONDecodeError as exc:
        return None, False, f"{exc.__class__.__name__}: {exc}"
    trailing = stripped[end:].strip()
    return payload, bool(trailing), None


def normalize_nested_schema_fields(payload: Any) -> tuple[Any, bool]:
    if not isinstance(payload, dict):
        return payload, False
    nested = payload.get("approved_plan_candidate")
    if not isinstance(nested, dict):
        return payload, False
    changed = False
    repaired = dict(payload)
    for field in REQUIRED_RESPONSE_SCHEMA_FIELDS:
        if field == "approved_plan_candidate":
            continue
        if field not in repaired and field in nested:
            repaired[field] = nested[field]
            changed = True
    plan = nested.get("plan")
    if isinstance(plan, dict):
        for field in REQUIRED_RESPONSE_SCHEMA_FIELDS:
            if field == "approved_plan_candidate":
                continue
            if field not in repaired and field in plan:
                repaired[field] = plan[field]
                changed = True
    return repaired, changed


def repair_hardened_response_text(text: str, scenario_id: str) -> HardenedOutputRepairResult:
    actions: list[str] = []
    candidate, changed = strip_markdown_code_fences(text)
    if changed:
        actions.append("strip_markdown_code_fences")
    payload, trailing, parse_error = decode_first_json_object(candidate)
    if parse_error:
        sanitized, sanitized_changed = sanitize_invalid_json_control_characters(candidate)
        if sanitized_changed:
            actions.append("sanitize_invalid_json_control_characters")
            payload, trailing, parse_error = decode_first_json_object(sanitized)
    if parse_error:
        return HardenedOutputRepairResult(
            scenario_id=scenario_id,
            status="failed",
            schema_valid=False,
            repair_actions_applied=tuple(actions),
            parse_error=parse_error,
            schema_errors=("json_parse_failed",),
            repaired_payload=None,
        )
    actions.append("json_raw_decode_first_object")
    if trailing:
        actions.append("trim_trailing_extra_data")
    payload, normalized = normalize_nested_schema_fields(payload)
    if normalized:
        actions.append("normalize_approved_plan_candidate_nested_schema_fields")
    if not isinstance(payload, dict):
        return HardenedOutputRepairResult(
            scenario_id=scenario_id,
            status="failed",
            schema_valid=False,
            repair_actions_applied=tuple(actions),
            parse_error=None,
            schema_errors=("repaired payload is not an object",),
            repaired_payload=None,
        )
    schema_errors = tuple(validate_hardened_response_payload(payload, scenario_id))
    return HardenedOutputRepairResult(
        scenario_id=scenario_id,
        status="ready" if not schema_errors else "failed",
        schema_valid=not schema_errors,
        repair_actions_applied=tuple(actions),
        parse_error=None,
        schema_errors=schema_errors,
        repaired_payload=payload,
    )


def validate_hardened_output_repair_contract(contract: HardenedOutputRepairContract = S13E_REPAIR_CONTRACT) -> list[str]:
    errors: list[str] = []
    s13d = live_benchmark_prompt_schema_hardening_report()
    if s13d.get("status") != "ready":
        errors.append("S13e requires S13d prompt/schema hardening contract to be ready")
    if contract.workflow_id != S13E_WORKFLOW_ID:
        errors.append("workflow_id must be slides.hardened_output_repair_parser")
    if contract.route != PUBLIC_API_DEV_ROUTE or contract.provider != REQUIRED_PROVIDER:
        errors.append("S13e route/provider mismatch")
    if contract.scenario_count != 12:
        errors.append("S13e must cover 12 selected benchmark scenarios")
    for action in REPAIR_ACTIONS:
        if action not in contract.repair_actions:
            errors.append(f"missing repair action: {action}")
    for requirement in REPAIR_INPUT_REQUIREMENTS:
        if requirement not in contract.input_requirements:
            errors.append(f"missing input requirement: {requirement}")
    for output in REPAIR_OUTPUTS:
        if output not in contract.required_outputs:
            errors.append(f"missing output: {output}")
    for action in FORBIDDEN_S13E_ACTIONS:
        if action not in contract.forbidden_actions:
            errors.append(f"missing forbidden action: {action}")
    must_be_true = {
        "requires_prior_s13d_hardened_live_rerun": contract.requires_prior_s13d_hardened_live_rerun,
        "deterministic_repair_only": contract.deterministic_repair_only,
        "preserves_original_response_digest": contract.preserves_original_response_digest,
        "writes_repair_manifest": contract.writes_repair_manifest,
    }
    for name, value in must_be_true.items():
        if value is not True:
            errors.append(f"{name} must be true")
    must_be_false = {
        "live_gigachat_call_allowed_by_s13e": contract.live_gigachat_call_allowed_by_s13e,
        "completed_human_review_results_present": contract.completed_human_review_results_present,
        "selected_parity_claim_supported_now": contract.selected_parity_claim_supported_now,
        "server3_local_intranet_verified": contract.server3_local_intranet_verified,
        "kimi_level_claimed": contract.kimi_level_claimed,
    }
    for name, value in must_be_false.items():
        if value is not False:
            errors.append(f"{name} must be false")
    return errors


def hardened_output_repair_report() -> dict[str, Any]:
    contract = S13E_REPAIR_CONTRACT
    errors = validate_hardened_output_repair_contract(contract)
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S13E_WORKFLOW_ID,
        "s_phase": S13E_PHASE_ID,
        "hardened_output_repair_parser_ready_by_s13e": not errors,
        "scenario_count": contract.scenario_count,
        "repair_actions": list(contract.repair_actions),
        "input_requirements": list(contract.input_requirements),
        "required_outputs": list(contract.required_outputs),
        "requires_prior_s13d_hardened_live_rerun_by_s13e": contract.requires_prior_s13d_hardened_live_rerun,
        "deterministic_repair_only_by_s13e": contract.deterministic_repair_only,
        "live_gigachat_call_allowed_by_s13e": contract.live_gigachat_call_allowed_by_s13e,
        "preserves_original_response_digest_by_s13e": contract.preserves_original_response_digest,
        "completed_human_review_results_present_by_s13e": contract.completed_human_review_results_present,
        "selected_offline_workflow_parity_claim_supported_now_by_s13e": contract.selected_parity_claim_supported_now,
        "server3_local_intranet_route_verified_by_s13e": contract.server3_local_intranet_verified,
        "kimi_level_claimed_by_s13e": contract.kimi_level_claimed,
        "whole_project_kimi_level_supported": False,
        "public_internet_required_by_s13e": False,
        "credential_values_recorded_by_s13e": False,
        "api_endpoint_added_by_s13e": False,
        "db_schema_migration_added_by_s13e": False,
        "frontend_runtime_changed_by_s13e": False,
        "dependency_versions_changed_by_s13e": False,
        "dockerfiles_changed_by_s13e": False,
        "next_recommended_step": "Run S13e repair on the failed S13d hardened rerun ZIP; if 12/12 schema-valid, export a repaired evidence packet for human review, otherwise do S13f prompt rerun.",
        "contract": contract.as_dict(),
        "errors": errors,
    }
