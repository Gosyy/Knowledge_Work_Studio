from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.kimi_style_benchmark import (
    REQUIRED_AUTOMATED_EVIDENCE,
    REQUIRED_HUMAN_REVIEW_DIMENSIONS,
    REQUIRED_S_PHASE_EVIDENCE,
    S10_SCENARIO_IDS,
)
from backend.app.services.slides_service.live_gigachat_selected_benchmark import (
    PUBLIC_API_DEV_ROUTE,
    REQUIRED_PROVIDER,
    live_gigachat_selected_benchmark_report,
)
from backend.app.services.slides_service.live_gigachat_evidence_packet import live_gigachat_evidence_packet_export_report

S13D_WORKFLOW_ID = "slides.live_benchmark_prompt_schema_hardening"
S13D_PHASE_ID = "S13d"
HARDENED_GENERATION_STATE = "awaiting_hardened_live_public_api_dev_generation"
POST_HARDENED_GENERATION_STATE = "hardened_generated_artifacts_ready"

REQUIRED_PROMPT_SECTIONS = (
    "strict_json_object_contract",
    "scenario_specific_benchmark_context",
    "slide_outline_and_storyline",
    "native_visual_plan",
    "citation_manifest_plan",
    "render_qa_obligations",
    "evidence_manifest_plan",
    "human_review_handoff",
    "claim_safety_guardrails",
)

REQUIRED_RESPONSE_SCHEMA_FIELDS = (
    "scenario_id",
    "title",
    "scenario_summary",
    "approved_plan_candidate",
    "slide_outline",
    "native_visuals",
    "citation_obligations",
    "render_qa_obligations",
    "evidence_manifest",
    "human_review_handoff",
    "safety_boundaries",
)

REQUIRED_SLIDE_FIELDS = (
    "slide_id",
    "title",
    "purpose",
    "source_grounding_required",
    "native_visuals",
    "citation_requirements",
    "render_qa_checks",
)

REQUIRED_NATIVE_VISUAL_TYPES = (
    "pptx_table",
    "pptx_chart",
    "pptx_shape_diagram",
)

REQUIRED_RENDER_QA_CHECKS = (
    "title_body_collision",
    "text_box_overlap",
    "clipped_text",
    "tiny_text",
    "table_overflow",
    "dense_native_visual_region",
    "chart_label_collision",
    "diagram_node_overlap",
    "citation_marker_visibility",
)

FORBIDDEN_S13D_ACTIONS = (
    "claim_kimi_level_achieved",
    "claim_selected_parity_from_generation_only",
    "claim_server3_local_intranet_verified",
    "complete_human_review_automatically",
    "auto_approve_scenarios",
    "record_raw_credentials",
)

MIN_REQUIRED_SLIDES_PER_SCENARIO = 8


@dataclass(frozen=True)
class HardenedPromptSchemaPolicy:
    scenario_id: str
    route: str
    provider: str
    required_prompt_sections: tuple[str, ...]
    required_response_schema_fields: tuple[str, ...]
    required_slide_fields: tuple[str, ...]
    required_native_visual_types: tuple[str, ...]
    required_render_qa_checks: tuple[str, ...]
    required_s_phase_evidence: tuple[str, ...]
    required_automated_evidence: tuple[str, ...]
    required_human_review_dimensions: tuple[str, ...]
    minimum_slide_count: int
    requires_strict_json: bool = True
    requires_scenario_specificity: bool = True
    requires_native_visuals: bool = True
    requires_slide_level_citations: bool = True
    requires_render_qa: bool = True
    requires_human_review_handoff: bool = True
    credential_values_recorded: bool = False
    completed_human_review_results_present: bool = False
    selected_parity_claim_supported_now: bool = False
    server3_local_intranet_verified: bool = False
    kimi_level_claimed: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "required_prompt_sections",
            "required_response_schema_fields",
            "required_slide_fields",
            "required_native_visual_types",
            "required_render_qa_checks",
            "required_s_phase_evidence",
            "required_automated_evidence",
            "required_human_review_dimensions",
        ):
            payload[key] = list(payload[key])
        return payload


def build_hardened_prompt_schema_policies() -> tuple[HardenedPromptSchemaPolicy, ...]:
    return tuple(
        HardenedPromptSchemaPolicy(
            scenario_id=scenario_id,
            route=PUBLIC_API_DEV_ROUTE,
            provider=REQUIRED_PROVIDER,
            required_prompt_sections=REQUIRED_PROMPT_SECTIONS,
            required_response_schema_fields=REQUIRED_RESPONSE_SCHEMA_FIELDS,
            required_slide_fields=REQUIRED_SLIDE_FIELDS,
            required_native_visual_types=REQUIRED_NATIVE_VISUAL_TYPES,
            required_render_qa_checks=REQUIRED_RENDER_QA_CHECKS,
            required_s_phase_evidence=REQUIRED_S_PHASE_EVIDENCE,
            required_automated_evidence=REQUIRED_AUTOMATED_EVIDENCE,
            required_human_review_dimensions=REQUIRED_HUMAN_REVIEW_DIMENSIONS,
            minimum_slide_count=MIN_REQUIRED_SLIDES_PER_SCENARIO,
        )
        for scenario_id in S10_SCENARIO_IDS
    )


HARDENED_PROMPT_SCHEMA_POLICIES = build_hardened_prompt_schema_policies()


def hardened_prompt_for_scenario(scenario_id: str) -> str:
    if scenario_id not in S10_SCENARIO_IDS:
        raise ValueError(f"unknown S10 scenario: {scenario_id}")
    schema = {
        "scenario_id": scenario_id,
        "title": "string",
        "scenario_summary": "scenario-specific one paragraph summary",
        "approved_plan_candidate": {
            "storyline": ["problem/context", "source-backed analysis", "decision or learning arc", "operator next actions"],
            "assumptions_to_verify": ["list concrete assumptions that require source evidence"],
            "non_goals": ["no approval", "no Kimi-level claim", "no Server 3 proof"],
        },
        "slide_outline": [
            {
                "slide_id": "s01",
                "title": "scenario-specific title",
                "purpose": "why this slide is needed",
                "source_grounding_required": True,
                "native_visuals": ["pptx_table | pptx_chart | pptx_shape_diagram | text_box"],
                "citation_requirements": ["claim_to_source_fragment_mapping_required"],
                "render_qa_checks": list(REQUIRED_RENDER_QA_CHECKS[:5]),
            }
        ],
        "native_visuals": [
            {
                "visual_id": "v01",
                "visual_type": "pptx_table | pptx_chart | pptx_shape_diagram",
                "editable_pptx_native": True,
                "source_fields_required": ["source_id", "fragment_id", "data_range_or_claim_id"],
                "render_qa_checks": list(REQUIRED_RENDER_QA_CHECKS),
            }
        ],
        "citation_obligations": {
            "slide_level_claims_require_sources": True,
            "native_visuals_require_sources": True,
            "minimum_citation_coverage": 1.0,
        },
        "render_qa_obligations": {
            "actual_slide_render_required": True,
            "geometry_manifest_required": True,
            "blocker_defect_can_fail_review": True,
            "checks": list(REQUIRED_RENDER_QA_CHECKS),
        },
        "evidence_manifest": {
            "required_outputs": list(REQUIRED_AUTOMATED_EVIDENCE),
            "required_s_phase_evidence": list(REQUIRED_S_PHASE_EVIDENCE),
        },
        "human_review_handoff": {
            "review_state": "pending_human_review",
            "review_dimensions": list(REQUIRED_HUMAN_REVIEW_DIMENSIONS),
            "allowed_decisions": ["approve", "request_rework", "reject"],
            "do_not_auto_fill": True,
        },
        "safety_boundaries": {
            "selected_parity_claim_supported_now": False,
            "kimi_level_claimed": False,
            "server3_local_intranet_verified": False,
            "completed_human_review_results_present": False,
            "credential_values_recorded": False,
        },
    }
    return (
        "You are producing a KW Studio S13d hardened selected benchmark generation plan. "
        "Return a single valid JSON object only, no markdown, no prose outside JSON. "
        f"Scenario id: {scenario_id}. Route: public_api_dev. Provider: GigaChat. "
        f"The JSON MUST contain at least {MIN_REQUIRED_SLIDES_PER_SCENARIO} slide_outline entries. "
        "Every slide must be scenario-specific and must include source grounding, native visuals or text-box rationale, citations, and render QA checks. "
        "Do not approve the scenario. Do not claim Kimi-level. Do not claim selected parity. Do not claim Server 3 local_intranet verification. "
        "Use this exact top-level schema and fill it with scenario-specific content: "
        + json.dumps(schema, ensure_ascii=False, sort_keys=True)
    )


def validate_hardened_response_payload(payload: Any, scenario_id: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["response must be a JSON object"]
    for field in REQUIRED_RESPONSE_SCHEMA_FIELDS:
        if field not in payload:
            errors.append(f"missing response field: {field}")
    if payload.get("scenario_id") != scenario_id:
        errors.append("scenario_id mismatch")
    slides = payload.get("slide_outline")
    if not isinstance(slides, list) or len(slides) < MIN_REQUIRED_SLIDES_PER_SCENARIO:
        errors.append(f"slide_outline must contain at least {MIN_REQUIRED_SLIDES_PER_SCENARIO} slides")
    elif isinstance(slides, list):
        for index, slide in enumerate(slides, start=1):
            if not isinstance(slide, dict):
                errors.append(f"slide {index} must be an object")
                continue
            for field in REQUIRED_SLIDE_FIELDS:
                if field not in slide:
                    errors.append(f"slide {index} missing field: {field}")
    safety = payload.get("safety_boundaries")
    if not isinstance(safety, dict):
        errors.append("safety_boundaries must be an object")
    else:
        for name in (
            "selected_parity_claim_supported_now",
            "kimi_level_claimed",
            "server3_local_intranet_verified",
            "completed_human_review_results_present",
            "credential_values_recorded",
        ):
            if safety.get(name) is not False:
                errors.append(f"safety_boundaries.{name} must be false")
    return errors


def validate_hardened_prompt_schema_contract() -> list[str]:
    errors: list[str] = []
    s13b = live_gigachat_selected_benchmark_report({})
    s13c = live_gigachat_evidence_packet_export_report()
    if s13b.get("status") != "ready":
        errors.append("S13d requires S13b live workflow contract to be ready")
    if s13c.get("status") != "ready":
        errors.append("S13d requires S13c evidence packet export contract to be ready")
    if len(HARDENED_PROMPT_SCHEMA_POLICIES) != 12:
        errors.append(f"expected 12 hardened prompt policies, got {len(HARDENED_PROMPT_SCHEMA_POLICIES)}")
    by_id = {policy.scenario_id: policy for policy in HARDENED_PROMPT_SCHEMA_POLICIES}
    for scenario_id in S10_SCENARIO_IDS:
        policy = by_id.get(scenario_id)
        if policy is None:
            errors.append(f"missing hardened prompt policy: {scenario_id}")
            continue
        if policy.route != PUBLIC_API_DEV_ROUTE or policy.provider != REQUIRED_PROVIDER:
            errors.append(f"{scenario_id}: route/provider mismatch")
        if policy.minimum_slide_count < MIN_REQUIRED_SLIDES_PER_SCENARIO:
            errors.append(f"{scenario_id}: minimum slide count is too low")
        for section in REQUIRED_PROMPT_SECTIONS:
            if section not in policy.required_prompt_sections:
                errors.append(f"{scenario_id}: missing prompt section {section}")
        for field in REQUIRED_RESPONSE_SCHEMA_FIELDS:
            if field not in policy.required_response_schema_fields:
                errors.append(f"{scenario_id}: missing schema field {field}")
        for value_name, value in {
            "requires_strict_json": policy.requires_strict_json,
            "requires_scenario_specificity": policy.requires_scenario_specificity,
            "requires_native_visuals": policy.requires_native_visuals,
            "requires_slide_level_citations": policy.requires_slide_level_citations,
            "requires_render_qa": policy.requires_render_qa,
            "requires_human_review_handoff": policy.requires_human_review_handoff,
        }.items():
            if value is not True:
                errors.append(f"{scenario_id}: {value_name} must be true")
        for value_name, value in {
            "credential_values_recorded": policy.credential_values_recorded,
            "completed_human_review_results_present": policy.completed_human_review_results_present,
            "selected_parity_claim_supported_now": policy.selected_parity_claim_supported_now,
            "server3_local_intranet_verified": policy.server3_local_intranet_verified,
            "kimi_level_claimed": policy.kimi_level_claimed,
        }.items():
            if value is not False:
                errors.append(f"{scenario_id}: {value_name} must be false")
    return errors


def live_benchmark_prompt_schema_hardening_report() -> dict[str, Any]:
    errors = validate_hardened_prompt_schema_contract()
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S13D_WORKFLOW_ID,
        "s_phase": S13D_PHASE_ID,
        "live_benchmark_prompt_schema_hardening_ready_by_s13d": not errors,
        "hardened_prompt_policy_count": len(HARDENED_PROMPT_SCHEMA_POLICIES),
        "scenario_ids": list(S10_SCENARIO_IDS),
        "route_required_by_s13d": PUBLIC_API_DEV_ROUTE,
        "provider_required_by_s13d": REQUIRED_PROVIDER,
        "requires_shell_env_credentials_by_s13d_live": True,
        "hardened_live_rerun_performed_by_static_check": False,
        "strict_json_required_by_s13d": True,
        "minimum_slide_count_per_scenario_by_s13d": MIN_REQUIRED_SLIDES_PER_SCENARIO,
        "required_prompt_sections": list(REQUIRED_PROMPT_SECTIONS),
        "required_response_schema_fields": list(REQUIRED_RESPONSE_SCHEMA_FIELDS),
        "required_slide_fields": list(REQUIRED_SLIDE_FIELDS),
        "required_render_qa_checks": list(REQUIRED_RENDER_QA_CHECKS),
        "required_native_visual_types": list(REQUIRED_NATIVE_VISUAL_TYPES),
        "forbidden_actions": list(FORBIDDEN_S13D_ACTIONS),
        "completed_human_review_results_present_by_s13d": False,
        "human_review_results_fabricated_by_s13d": False,
        "auto_approval_allowed_by_s13d": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13d": False,
        "selected_offline_workflow_parity_claim_requires_future_completed_results_by_s13d": True,
        "server3_local_intranet_route_verified_by_s13d": False,
        "public_api_dev_route_is_not_server3_proof_by_s13d": True,
        "credential_values_recorded_by_s13d": False,
        "hidden_public_internet_allowed_by_s13d": False,
        "public_internet_required_for_live_s13d": True,
        "cloud_research_allowed_by_s13d": False,
        "cloud_vision_allowed_by_s13d": False,
        "kimi_level_claimed_by_s13d": False,
        "whole_project_kimi_level_supported": False,
        "api_endpoint_added_by_s13d": False,
        "db_schema_migration_added_by_s13d": False,
        "frontend_runtime_changed_by_s13d": False,
        "dependency_versions_changed_by_s13d": False,
        "dockerfiles_changed_by_s13d": False,
        "next_recommended_step": "Run the explicit S13d hardened live public_api_dev rerun command, export a new S13c evidence packet, then collect real human review results.",
        "contract": {
            "hardened_prompt_schema_policies": [policy.as_dict() for policy in HARDENED_PROMPT_SCHEMA_POLICIES],
        },
        "errors": errors,
    }
