from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.live_gigachat_selected_benchmark import PUBLIC_API_DEV_ROUTE, REQUIRED_PROVIDER
from backend.app.services.slides_service.strict_json_per_scenario_rerun import (
    MIN_REQUIRED_SLIDES_PER_SCENARIO,
    REQUIRED_RENDER_QA_CHECKS,
    strict_json_per_scenario_rerun_report,
)

S13G_WORKFLOW_ID = "slides.canonical_schema_adapter_minimal_rerun"
S13G_PHASE_ID = "S13g"
CANONICAL_SCHEMA_VERSION = "s13g.canonical_schema_adapter.v1"

MINIMAL_MODEL_FIELDS = (
    "scenario_id",
    "deck_title",
    "storyline",
    "slides",
    "risks_or_open_questions",
)

CANONICAL_REQUIRED_FIELDS = (
    "schema_name",
    "schema_version",
    "scenario_id",
    "provider",
    "route",
    "deck_title",
    "scenario_summary",
    "approved_plan_candidate",
    "slide_outline",
    "native_visuals",
    "citation_obligations",
    "render_qa_obligations",
    "evidence_manifest",
    "human_review_handoff",
    "adapter_provenance",
    "safety_boundaries",
)

ADAPTER_PROVENANCE_FIELDS = (
    "model_provided_fields",
    "adapter_added_fields",
    "normalization_actions",
    "original_model_payload_digest",
    "canonical_payload_digest",
)

ADAPTER_NORMALIZATION_ACTIONS = (
    "parse_minimal_model_json",
    "map_deck_title_to_title",
    "map_storyline_to_approved_plan_candidate",
    "normalize_slides_to_slide_outline",
    "add_required_workflow_metadata",
    "add_safety_boundaries",
    "add_human_review_handoff",
    "add_adapter_provenance",
)

FORBIDDEN_S13G_ACTIONS = (
    "treat_adapter_fields_as_model_generated",
    "fabricate_human_review_results",
    "auto_approve_scenarios",
    "claim_selected_offline_workflow_parity",
    "claim_kimi_level_achieved",
    "claim_server3_local_intranet_verified",
    "record_raw_credentials",
)


@dataclass(frozen=True)
class CanonicalAdapterScenarioPolicy:
    scenario_id: str
    route: str
    provider: str
    minimum_slide_count: int
    minimal_prompt_required: bool = True
    canonical_adapter_required: bool = True
    adapter_provenance_required: bool = True
    model_vs_adapter_field_separation_required: bool = True
    deterministic_normalization_required: bool = True
    static_check_calls_gigachat: bool = False
    completed_human_review_results_present: bool = False
    selected_parity_claim_supported_now: bool = False
    server3_local_intranet_verified: bool = False
    kimi_level_claimed: bool = False
    credential_values_recorded: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


CANONICAL_ADAPTER_POLICIES = tuple(
    CanonicalAdapterScenarioPolicy(
        scenario_id=scenario_id,
        route=PUBLIC_API_DEV_ROUTE,
        provider=REQUIRED_PROVIDER,
        minimum_slide_count=MIN_REQUIRED_SLIDES_PER_SCENARIO,
    )
    for scenario_id in S10_SCENARIO_IDS
)


def minimal_prompt_for_scenario(scenario_id: str) -> str:
    if scenario_id not in S10_SCENARIO_IDS:
        raise ValueError(f"unknown S10 scenario: {scenario_id}")
    minimal_schema = {
        "scenario_id": scenario_id,
        "deck_title": "short scenario-specific title",
        "storyline": [
            "context and audience",
            "source-backed analysis arc",
            "decision, recommendation, or learning arc",
            "operator next actions",
        ],
        "slides": [
            {
                "title": "scenario-specific slide title",
                "purpose": "why this slide is needed",
                "key_claims": ["claim that will need source grounding"],
                "visual_intent": "pptx_table | pptx_chart | pptx_shape_diagram | text_box",
                "citation_needs": ["claim_to_source_fragment_mapping_required"],
            }
        ],
        "risks_or_open_questions": ["list assumptions that require evidence or review"],
    }
    return (
        "Return exactly one small JSON object and nothing else. "
        "Do not echo a large schema. Do not use markdown fences. "
        f"Scenario id: {scenario_id}. "
        f"Provide at least {MIN_REQUIRED_SLIDES_PER_SCENARIO} slide objects. "
        "Each slide must include title, purpose, key_claims, visual_intent, and citation_needs. "
        "Do not approve the scenario. Do not claim Kimi-level, selected parity, or Server 3 local_intranet verification. "
        "Use this minimal schema only: "
        + json.dumps(minimal_schema, ensure_ascii=False, sort_keys=True)
    )


def _json_digest(payload: Any) -> str:
    import hashlib
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _coerce_slide(raw_slide: Any, *, scenario_id: str, index: int) -> tuple[dict[str, Any], list[str]]:
    actions: list[str] = []
    if not isinstance(raw_slide, dict):
        raw_slide = {"title": f"{scenario_id} slide {index}", "purpose": str(raw_slide)}
        actions.append("coerce_non_object_slide_to_object")
    title = str(raw_slide.get("title") or raw_slide.get("slide_title") or f"{scenario_id} slide {index}").strip()
    purpose = str(raw_slide.get("purpose") or raw_slide.get("objective") or raw_slide.get("why") or "").strip()
    if not purpose:
        purpose = f"Review-ready scenario-specific purpose for {scenario_id} slide {index}."
        actions.append("adapter_added_missing_slide_purpose")
    visual_intent = raw_slide.get("visual_intent") or raw_slide.get("visual") or raw_slide.get("native_visuals") or "text_box"
    native_visuals = _ensure_list(visual_intent)
    claims = _ensure_list(raw_slide.get("key_claims") or raw_slide.get("claims") or raw_slide.get("content"))
    if not claims:
        claims = [f"{scenario_id} slide {index} claim requires source grounding"]
        actions.append("adapter_added_claim_placeholder")
    citation_needs = _ensure_list(raw_slide.get("citation_needs") or raw_slide.get("citation_requirements"))
    if not citation_needs:
        citation_needs = ["claim_to_source_fragment_mapping_required"]
        actions.append("adapter_added_citation_requirement")
    slide = {
        "slide_id": f"s{index:02d}",
        "title": title,
        "purpose": purpose,
        "source_grounding_required": True,
        "native_visuals": [str(item) for item in native_visuals],
        "citation_requirements": [str(item) for item in citation_needs],
        "render_qa_checks": list(REQUIRED_RENDER_QA_CHECKS[:5]),
        "key_claims": [str(item) for item in claims],
        "adapter_normalized": bool(actions),
    }
    return slide, actions


def adapt_minimal_model_payload_to_canonical(payload: Any, scenario_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("minimal model payload must be a JSON object")
    model_fields = sorted(str(key) for key in payload.keys())
    adapter_added_fields: list[str] = []
    normalization_actions: list[str] = ["parse_minimal_model_json"]
    deck_title = str(payload.get("deck_title") or payload.get("title") or f"{scenario_id} benchmark deck").strip()
    if "deck_title" not in payload:
        adapter_added_fields.append("deck_title")
        normalization_actions.append("map_title_or_default_to_deck_title")
    storyline = [str(item) for item in _ensure_list(payload.get("storyline"))]
    if not storyline:
        storyline = ["context and audience", "source-backed analysis arc", "decision or learning arc", "operator next actions"]
        adapter_added_fields.append("approved_plan_candidate.storyline")
        normalization_actions.append("adapter_added_default_storyline")
    raw_slides = _ensure_list(payload.get("slides") or payload.get("slide_outline"))
    while len(raw_slides) < MIN_REQUIRED_SLIDES_PER_SCENARIO:
        raw_slides.append(
            {
                "title": f"{scenario_id} slide {len(raw_slides) + 1}",
                "purpose": f"Adapter-added required slide for {scenario_id}.",
                "key_claims": [f"{scenario_id} claim requires evidence"],
                "visual_intent": "text_box",
                "citation_needs": ["claim_to_source_fragment_mapping_required"],
            }
        )
        adapter_added_fields.append("slide_outline")
        normalization_actions.append("adapter_padded_slide_outline_to_minimum")
    slides: list[dict[str, Any]] = []
    for index, raw_slide in enumerate(raw_slides, start=1):
        slide, actions = _coerce_slide(raw_slide, scenario_id=scenario_id, index=index)
        slides.append(slide)
        normalization_actions.extend(actions)
    native_visual_types = sorted({str(item) for slide in slides for item in slide.get("native_visuals", [])}) or ["text_box"]
    canonical = {
        "schema_name": "kw_s13g_canonical_selected_benchmark_plan",
        "schema_version": CANONICAL_SCHEMA_VERSION,
        "scenario_id": scenario_id,
        "provider": REQUIRED_PROVIDER,
        "route": PUBLIC_API_DEV_ROUTE,
        "deck_title": deck_title,
        "scenario_summary": str(payload.get("scenario_summary") or payload.get("summary") or f"Canonical adapted benchmark plan for {scenario_id}."),
        "approved_plan_candidate": {
            "storyline": storyline,
            "assumptions_to_verify": [str(item) for item in _ensure_list(payload.get("risks_or_open_questions"))],
            "non_goals": ["no auto approval", "no Kimi-level claim", "no Server 3 local_intranet proof"],
        },
        "slide_outline": slides,
        "native_visuals": [
            {
                "visual_id": f"v{idx:02d}",
                "visual_type": str(visual_type),
                "editable_pptx_native": visual_type != "raster_only",
                "source_fields_required": ["source_id", "fragment_id", "claim_id"],
                "render_qa_checks": list(REQUIRED_RENDER_QA_CHECKS),
            }
            for idx, visual_type in enumerate(native_visual_types, start=1)
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
            "required_outputs": [
                "approved_plan_candidate_json",
                "artifact_generation_request_json",
                "safe_metadata_json",
                "citation_manifest_placeholder_json",
                "render_qa_input_placeholder_json",
            ],
            "model_payload_digest": _json_digest(payload),
        },
        "human_review_handoff": {
            "review_state": "pending_human_review",
            "allowed_decisions": ["approve", "request_rework", "reject"],
            "do_not_auto_fill": True,
        },
        "adapter_provenance": {
            "model_provided_fields": model_fields,
            "adapter_added_fields": sorted(set(adapter_added_fields + [
                "schema_name",
                "schema_version",
                "provider",
                "route",
                "citation_obligations",
                "render_qa_obligations",
                "human_review_handoff",
                "safety_boundaries",
            ])),
            "normalization_actions": sorted(set(normalization_actions + list(ADAPTER_NORMALIZATION_ACTIONS))),
            "original_model_payload_digest": _json_digest(payload),
            "canonical_payload_digest": "",
            "adapter_fields_are_not_model_generated": True,
        },
        "safety_boundaries": {
            "selected_parity_claim_supported_now": False,
            "kimi_level_claimed": False,
            "server3_local_intranet_verified": False,
            "completed_human_review_results_present": False,
            "credential_values_recorded": False,
        },
    }
    canonical["adapter_provenance"]["canonical_payload_digest"] = _json_digest({k: v for k, v in canonical.items() if k != "adapter_provenance"})
    return canonical


def validate_canonical_s13g_payload(payload: Any, scenario_id: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["canonical payload must be a JSON object"]
    for field in CANONICAL_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"missing canonical field: {field}")
    if payload.get("scenario_id") != scenario_id:
        errors.append("scenario_id mismatch")
    if payload.get("route") != PUBLIC_API_DEV_ROUTE or payload.get("provider") != REQUIRED_PROVIDER:
        errors.append("route/provider mismatch")
    slides = payload.get("slide_outline")
    if not isinstance(slides, list) or len(slides) < MIN_REQUIRED_SLIDES_PER_SCENARIO:
        errors.append(f"slide_outline must contain at least {MIN_REQUIRED_SLIDES_PER_SCENARIO} slides")
    elif isinstance(slides, list):
        for index, slide in enumerate(slides, start=1):
            if not isinstance(slide, dict):
                errors.append(f"slide {index} must be an object")
                continue
            for field in ("slide_id", "title", "purpose", "source_grounding_required", "native_visuals", "citation_requirements", "render_qa_checks"):
                if field not in slide:
                    errors.append(f"slide {index} missing field: {field}")
            if not str(slide.get("purpose") or "").strip():
                errors.append(f"slide {index} purpose must be non-empty")
            if slide.get("source_grounding_required") is not True:
                errors.append(f"slide {index} source_grounding_required must be true")
    provenance = payload.get("adapter_provenance")
    if not isinstance(provenance, dict):
        errors.append("adapter_provenance must be an object")
    else:
        for field in ADAPTER_PROVENANCE_FIELDS:
            if field not in provenance:
                errors.append(f"adapter_provenance missing field: {field}")
        if provenance.get("adapter_fields_are_not_model_generated") is not True:
            errors.append("adapter provenance must mark adapter fields as not model-generated")
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


def validate_canonical_schema_adapter_contract() -> list[str]:
    errors: list[str] = []
    s13f = strict_json_per_scenario_rerun_report()
    if s13f.get("status") != "ready":
        errors.append("S13g requires S13f strict JSON rerun contract to be ready")
    if len(CANONICAL_ADAPTER_POLICIES) != 12:
        errors.append("S13g must cover 12 selected benchmark scenarios")
    sample = {
        "scenario_id": S10_SCENARIO_IDS[0],
        "deck_title": "sample deck",
        "storyline": ["context", "analysis", "decision", "actions"],
        "slides": [
            {
                "title": f"Slide {idx}",
                "purpose": f"Purpose {idx}",
                "key_claims": ["claim"],
                "visual_intent": "pptx_table",
                "citation_needs": ["source fragment"],
            }
            for idx in range(1, MIN_REQUIRED_SLIDES_PER_SCENARIO + 1)
        ],
        "risks_or_open_questions": ["source coverage"],
    }
    sample_errors = validate_canonical_s13g_payload(adapt_minimal_model_payload_to_canonical(sample, S10_SCENARIO_IDS[0]), S10_SCENARIO_IDS[0])
    if sample_errors:
        errors.append(f"S13g sample adapted payload failed validation: {sample_errors[:3]}")
    for policy in CANONICAL_ADAPTER_POLICIES:
        if policy.route != PUBLIC_API_DEV_ROUTE or policy.provider != REQUIRED_PROVIDER:
            errors.append(f"{policy.scenario_id}: route/provider mismatch")
        for name, value in {
            "minimal_prompt_required": policy.minimal_prompt_required,
            "canonical_adapter_required": policy.canonical_adapter_required,
            "adapter_provenance_required": policy.adapter_provenance_required,
            "model_vs_adapter_field_separation_required": policy.model_vs_adapter_field_separation_required,
            "deterministic_normalization_required": policy.deterministic_normalization_required,
        }.items():
            if value is not True:
                errors.append(f"{policy.scenario_id}: {name} must be true")
        for name, value in {
            "static_check_calls_gigachat": policy.static_check_calls_gigachat,
            "completed_human_review_results_present": policy.completed_human_review_results_present,
            "selected_parity_claim_supported_now": policy.selected_parity_claim_supported_now,
            "server3_local_intranet_verified": policy.server3_local_intranet_verified,
            "kimi_level_claimed": policy.kimi_level_claimed,
            "credential_values_recorded": policy.credential_values_recorded,
        }.items():
            if value is not False:
                errors.append(f"{policy.scenario_id}: {name} must be false")
    return errors


def canonical_schema_adapter_report() -> dict[str, Any]:
    errors = validate_canonical_schema_adapter_contract()
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S13G_WORKFLOW_ID,
        "s_phase": S13G_PHASE_ID,
        "canonical_schema_adapter_ready_by_s13g": not errors,
        "scenario_count": len(CANONICAL_ADAPTER_POLICIES),
        "route_required_by_s13g": PUBLIC_API_DEV_ROUTE,
        "provider_required_by_s13g": REQUIRED_PROVIDER,
        "minimal_prompt_required_by_s13g": True,
        "canonical_adapter_required_by_s13g": True,
        "adapter_provenance_required_by_s13g": True,
        "model_vs_adapter_field_separation_required_by_s13g": True,
        "deterministic_normalization_required_by_s13g": True,
        "minimum_slide_count_per_scenario_by_s13g": MIN_REQUIRED_SLIDES_PER_SCENARIO,
        "static_check_calls_gigachat_by_s13g": False,
        "completed_human_review_results_present_by_s13g": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13g": False,
        "server3_local_intranet_route_verified_by_s13g": False,
        "public_api_dev_route_is_not_server3_proof_by_s13g": True,
        "credential_values_recorded_by_s13g": False,
        "kimi_level_claimed_by_s13g": False,
        "whole_project_kimi_level_supported": False,
        "api_endpoint_added_by_s13g": False,
        "db_schema_migration_added_by_s13g": False,
        "frontend_runtime_changed_by_s13g": False,
        "dependency_versions_changed_by_s13g": False,
        "dockerfiles_changed_by_s13g": False,
        "next_recommended_step": "Run S13g minimal live rerun with shell env GigaChat credentials, adapt outputs to canonical schema, and export human-review packet only if 12/12 canonical-valid.",
        "contract": {
            "minimal_model_fields": list(MINIMAL_MODEL_FIELDS),
            "canonical_required_fields": list(CANONICAL_REQUIRED_FIELDS),
            "adapter_provenance_fields": list(ADAPTER_PROVENANCE_FIELDS),
            "normalization_actions": list(ADAPTER_NORMALIZATION_ACTIONS),
            "forbidden_actions": list(FORBIDDEN_S13G_ACTIONS),
            "policies": [policy.as_dict() for policy in CANONICAL_ADAPTER_POLICIES],
        },
        "errors": errors,
    }
