from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

S3_WORKFLOW_ID = "slides.adaptive_deck_modes"

DECK_MODE_IDS = (
    "executive_board_deck",
    "architecture_review_deck",
    "project_status_deck",
    "decision_matrix_deck",
    "long_document_explainer",
)

CORE_SLIDE_ARCHETYPES = (
    "title_context",
    "source_grounded_objective",
    "evidence_summary",
    "recommendation_or_decision",
    "next_actions",
)

KIMI_DERIVED_PATTERNS = (
    "outline_first",
    "editable_plan_before_generation",
    "mode_specific_storyline",
    "adaptive_slide_archetype_selection",
    "source_to_slide_provenance",
    "render_based_visual_qa_ready",
)


@dataclass(frozen=True)
class AdaptiveDeckMode:
    mode_id: str
    title: str
    source_intent: str
    storyline: tuple[str, ...]
    required_slide_archetypes: tuple[str, ...]
    table_chart_policy: str
    visual_qa_expectations: tuple[str, ...]
    provenance_expectations: tuple[str, ...]
    failure_guards: tuple[str, ...]
    recommended_render_mode: str = "adaptive"
    offline_ready: bool = True
    browser_required: bool = False
    public_internet_required: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "storyline",
            "required_slide_archetypes",
            "visual_qa_expectations",
            "provenance_expectations",
            "failure_guards",
        ):
            payload[key] = list(payload[key])
        return payload


ADAPTIVE_DECK_MODES: dict[str, AdaptiveDeckMode] = {
    "executive_board_deck": AdaptiveDeckMode(
        mode_id="executive_board_deck",
        title="Executive / board decision deck",
        source_intent="memo_or_brief_to_decision_deck",
        storyline=(
            "executive_context",
            "decision_required",
            "evidence_and_tradeoffs",
            "risk_guardrails",
            "recommendation",
            "owner_next_actions",
        ),
        required_slide_archetypes=(
            "executive_title",
            "decision_request",
            "readiness_evidence",
            "risk_guardrail_table",
            "recommendation_slide",
            "next_actions_owner_table",
        ),
        table_chart_policy="Use compact evidence/risk/action tables only when they support the decision.",
        visual_qa_expectations=(
            "title_not_truncated",
            "executive_summary_scannable",
            "no_generic_fallback_labels",
            "risk_table_not_overflowing",
        ),
        provenance_expectations=(
            "decision_claims_link_to_source_fragments",
            "risk_guardrails_link_to_source_fragments",
        ),
        failure_guards=(
            "forbid_k1_plan_titles",
            "forbid_additional_source_grounded_planning_point",
            "require_recommendation_or_decision_slide",
        ),
    ),
    "architecture_review_deck": AdaptiveDeckMode(
        mode_id="architecture_review_deck",
        title="Architecture review deck",
        source_intent="technical_architecture_doc_to_review_deck",
        storyline=(
            "topology_map",
            "production_path",
            "component_responsibilities",
            "runtime_boundaries",
            "failure_modes",
            "operator_gates",
            "release_readiness_owner_actions",
        ),
        required_slide_archetypes=(
            "architecture_title",
            "topology_map",
            "component_responsibility_matrix",
            "runtime_boundary_table",
            "failure_modes_operator_gates",
            "release_readiness_checklist",
            "owner_next_actions",
        ),
        table_chart_policy="Prefer topology/responsibility/failure-mode tables over arbitrary current-target splits.",
        visual_qa_expectations=(
            "no_title_body_overlap",
            "topology_table_readable",
            "failure_modes_operator_gates_visible",
            "no_repetitive_tail_slides",
        ),
        provenance_expectations=(
            "each_topology_claim_has_source_fragment",
            "each_boundary_claim_has_source_fragment",
            "each_failure_mode_links_to_operator_control",
        ),
        failure_guards=(
            "forbid_arbitrary_current_target_split",
            "require_failure_modes_operator_gates",
            "require_server_boundary_clarity",
        ),
    ),
    "project_status_deck": AdaptiveDeckMode(
        mode_id="project_status_deck",
        title="Project status deck",
        source_intent="project_log_to_status_review",
        storyline=(
            "status_snapshot",
            "milestone_timeline",
            "completed_workstreams",
            "current_risks",
            "open_decisions",
            "next_actions",
        ),
        required_slide_archetypes=(
            "status_title",
            "milestone_timeline",
            "readiness_summary",
            "risk_register",
            "open_decisions_table",
            "next_actions_owner_table",
        ),
        table_chart_policy="Use milestone/risk/action tables; preserve late-source milestones and closure evidence.",
        visual_qa_expectations=(
            "timeline_not_crowded",
            "risk_table_readable",
            "next_actions_visible",
            "no_missing_late_milestones",
        ),
        provenance_expectations=(
            "milestones_link_to_log_sections",
            "risks_link_to_source_notes",
            "next_actions_link_to_latest_source_entries",
        ),
        failure_guards=(
            "forbid_stopping_at_early_milestones",
            "require_risks_and_next_actions",
            "require_closure_or_current_state",
        ),
    ),
    "decision_matrix_deck": AdaptiveDeckMode(
        mode_id="decision_matrix_deck",
        title="Decision matrix deck",
        source_intent="comparison_table_to_decision_deck",
        storyline=(
            "decision_context",
            "options_matrix",
            "strengths_weaknesses",
            "constraints",
            "recommendation",
            "implementation_next_steps",
        ),
        required_slide_archetypes=(
            "decision_title",
            "option_matrix",
            "tradeoff_summary",
            "constraints_assumptions",
            "recommendation_slide",
            "implementation_next_steps",
        ),
        table_chart_policy="Parse rows/columns into an option matrix; never render raw CSV text as slide narrative.",
        visual_qa_expectations=(
            "matrix_columns_preserved",
            "table_not_overflowing",
            "recommendation_visually_prominent",
            "raw_csv_not_visible",
        ),
        provenance_expectations=(
            "each_option_links_to_source_row",
            "recommendation_links_to_table_evidence",
            "constraints_link_to_source_cells",
        ),
        failure_guards=(
            "forbid_raw_csv_header_title",
            "require_option_matrix",
            "require_explicit_recommendation",
        ),
    ),
    "long_document_explainer": AdaptiveDeckMode(
        mode_id="long_document_explainer",
        title="Long document structured explainer",
        source_intent="long_docx_pdf_to_structured_presentation",
        storyline=(
            "section_map",
            "core_concepts",
            "architecture_or_process_summary",
            "evidence_package",
            "risks_or_constraints",
            "claim_guard",
            "next_steps",
        ),
        required_slide_archetypes=(
            "document_title",
            "section_map",
            "key_concepts",
            "structured_summary_table",
            "evidence_package",
            "risk_or_constraint_table",
            "claim_guard",
            "next_steps",
        ),
        table_chart_policy="Use section maps, summary/risk tables, and evidence packages instead of filler slides.",
        visual_qa_expectations=(
            "section_map_scannable",
            "no_filler_slides",
            "evidence_package_readable",
            "claim_guard_visible",
        ),
        provenance_expectations=(
            "each_section_maps_to_source_range",
            "evidence_package_links_to_fragments",
            "claim_guard_links_to source constraints".replace("to source", "to_source"),
        ),
        failure_guards=(
            "forbid_additional_source_grounded_planning_point",
            "require_meaningful_source_derived_slide_per_target_slide",
            "require_claim_guard_when_sources_are_long",
        ),
    ),
}


def get_adaptive_deck_mode_registry() -> dict[str, AdaptiveDeckMode]:
    return dict(ADAPTIVE_DECK_MODES)


def validate_adaptive_deck_mode(mode: AdaptiveDeckMode) -> list[str]:
    errors: list[str] = []
    if mode.mode_id not in DECK_MODE_IDS:
        errors.append(f"unknown deck mode id: {mode.mode_id}")
    if mode.recommended_render_mode != "adaptive":
        errors.append(f"{mode.mode_id}: recommended render mode must be adaptive")
    if not mode.offline_ready:
        errors.append(f"{mode.mode_id}: offline_ready must be true")
    if mode.browser_required:
        errors.append(f"{mode.mode_id}: browser runtime must not be required")
    if mode.public_internet_required:
        errors.append(f"{mode.mode_id}: public internet must not be required")
    if len(mode.storyline) < 5:
        errors.append(f"{mode.mode_id}: storyline must contain at least five stages")
    if len(mode.required_slide_archetypes) < 5:
        errors.append(f"{mode.mode_id}: must define at least five slide archetypes")
    if not mode.table_chart_policy.strip():
        errors.append(f"{mode.mode_id}: table/chart policy is required")
    for archetype in CORE_SLIDE_ARCHETYPES[:3]:
        # Core concept coverage is intentionally semantic; mode-specific names may differ.
        if archetype == "title_context" and not any("title" in item for item in mode.required_slide_archetypes):
            errors.append(f"{mode.mode_id}: title archetype is required")
        if archetype == "evidence_summary" and not any("evidence" in item or "summary" in item or "matrix" in item for item in mode.required_slide_archetypes):
            errors.append(f"{mode.mode_id}: evidence/summary archetype is required")
    if not mode.visual_qa_expectations:
        errors.append(f"{mode.mode_id}: visual QA expectations are required")
    if not mode.provenance_expectations:
        errors.append(f"{mode.mode_id}: provenance expectations are required")
    if not mode.failure_guards:
        errors.append(f"{mode.mode_id}: failure guards are required")
    if any("k1_plan" in guard.lower() or "filler" in guard.lower() for guard in mode.failure_guards):
        # positive: at least one guard catches known P9/P10 failure mode
        pass
    return errors


def validate_adaptive_deck_mode_registry(registry: dict[str, AdaptiveDeckMode] | None = None) -> list[str]:
    registry = registry or ADAPTIVE_DECK_MODES
    errors: list[str] = []
    for mode_id in DECK_MODE_IDS:
        if mode_id not in registry:
            errors.append(f"missing adaptive deck mode: {mode_id}")
    for mode in registry.values():
        errors.extend(validate_adaptive_deck_mode(mode))

    decision = registry.get("decision_matrix_deck")
    if decision and "option_matrix" not in decision.required_slide_archetypes:
        errors.append("decision_matrix_deck must require option_matrix")
    architecture = registry.get("architecture_review_deck")
    if architecture and "failure_modes_operator_gates" not in architecture.required_slide_archetypes:
        errors.append("architecture_review_deck must require failure_modes_operator_gates")
    status = registry.get("project_status_deck")
    if status and not any("risk" in item for item in status.required_slide_archetypes):
        errors.append("project_status_deck must include a risk archetype")
    long_doc = registry.get("long_document_explainer")
    if long_doc and not any("claim_guard" == item for item in long_doc.required_slide_archetypes):
        errors.append("long_document_explainer must include claim_guard")
    return errors


def adaptive_deck_modes_report() -> dict[str, Any]:
    registry = get_adaptive_deck_mode_registry()
    errors = validate_adaptive_deck_mode_registry(registry)
    mode_payload = {mode_id: mode.as_dict() for mode_id, mode in sorted(registry.items())}
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S3_WORKFLOW_ID,
        "s_phase": "S3",
        "adaptive_deck_mode_count": len(registry),
        "expected_adaptive_deck_mode_count": len(DECK_MODE_IDS),
        "adaptive_deck_mode_ids": list(DECK_MODE_IDS),
        "mode_registry": mode_payload,
        "mode_specific_storyline_required_by_s3": True,
        "slide_archetype_registry_ready_by_s3": not errors,
        "table_chart_policy_ready_for_s4": not errors,
        "visual_qa_expectations_ready_for_s9": not errors,
        "source_to_slide_provenance_required_by_s3": True,
        "offline_ready_by_s3": all(mode.offline_ready for mode in registry.values()),
        "public_internet_required_by_s3": False,
        "browser_runtime_required_by_s3": False,
        "api_endpoint_added_by_s3": False,
        "db_schema_migration_added_by_s3": False,
        "frontend_runtime_changed_by_s3": False,
        "dependency_versions_changed_by_s3": False,
        "dockerfiles_changed_by_s3": False,
        "cloud_llm_added_by_s3": False,
        "cloud_vision_added_by_s3": False,
        "kimi_level_claimed_by_s3": False,
        "whole_project_kimi_level_supported": False,
        "server3_local_intranet_route_verified_by_s3": False,
        "next_recommended_step": "S4 - native table/chart/diagram rendering from mode-specific archetypes.",
        "errors": errors,
    }
