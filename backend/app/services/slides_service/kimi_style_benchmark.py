from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

S10_WORKFLOW_ID = "slides.kimi_style_benchmark"

S10_SCENARIO_IDS = (
    "executive_memo_to_board_deck",
    "architecture_doc_to_architecture_review",
    "project_log_to_status_deck",
    "comparison_table_to_decision_matrix",
    "long_doc_to_structured_explainer",
    "research_report_to_cited_deck",
    "kpi_spreadsheet_to_business_review",
    "product_launch_brief_to_launch_deck",
    "training_material_to_training_deck",
    "screenshot_to_editable_slide",
    "branded_template_to_brand_deck",
    "browser_evidence_packet_to_cited_deck",
)

REQUIRED_S_PHASE_EVIDENCE = (
    "S1_gap_dossier",
    "S2_outline_first_frontend_workflow",
    "S3_adaptive_deck_modes",
    "S4_native_table_chart_diagram_rendering",
    "S5_template_master_ingestion",
    "S6_image_screenshot_to_slide_workflow",
    "S7_offline_intranet_research_citations",
    "S8_conversational_edit_loop",
    "S9_render_based_visual_qa",
)

REQUIRED_HUMAN_REVIEW_DIMENSIONS = (
    "storyline_quality",
    "source_grounding",
    "layout_visual_quality",
    "native_visual_editability",
    "citation_usefulness",
    "operator_workflow_fit",
)

REQUIRED_AUTOMATED_EVIDENCE = (
    "approved_plan_snapshot",
    "generated_pptx",
    "artifact_manifest",
    "safe_metadata",
    "citation_manifest",
    "render_geometry_manifest",
    "render_based_visual_qa_report",
)

ACCEPTED_FINAL_CLAIM_WORDING = (
    "Kimi Slides-class offline workflow parity for selected benchmark scenarios."
)


@dataclass(frozen=True)
class KimiStyleBenchmarkScenario:
    scenario_id: str
    title: str
    source_types: tuple[str, ...]
    required_s_phase_evidence: tuple[str, ...]
    required_outputs: tuple[str, ...]
    human_review_dimensions: tuple[str, ...]
    acceptance_focus: tuple[str, ...]
    offline_ready: bool = True
    public_internet_required: bool = False
    cloud_vision_required: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "source_types",
            "required_s_phase_evidence",
            "required_outputs",
            "human_review_dimensions",
            "acceptance_focus",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True)
class KimiStyleBenchmarkAcceptancePolicy:
    required_scenario_count: int
    minimum_approved_scenario_count: int
    rejects_allowed: int
    blocker_defects_allowed: int
    request_rework_allowed_for_parity_claim: int
    minimum_citation_coverage: float
    minimum_render_visual_qa_pass_rate: float
    requires_completed_human_review: bool
    requires_render_based_visual_qa: bool
    requires_offline_intranet_source_boundary: bool
    requires_selected_parity_wording: bool
    accepted_final_claim_wording: str
    whole_project_kimi_level_claim_allowed: bool
    generic_kimi_level_achieved_claim_allowed: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _scenario(
    scenario_id: str,
    title: str,
    source_types: tuple[str, ...],
    acceptance_focus: tuple[str, ...],
) -> KimiStyleBenchmarkScenario:
    return KimiStyleBenchmarkScenario(
        scenario_id=scenario_id,
        title=title,
        source_types=source_types,
        required_s_phase_evidence=REQUIRED_S_PHASE_EVIDENCE,
        required_outputs=REQUIRED_AUTOMATED_EVIDENCE,
        human_review_dimensions=REQUIRED_HUMAN_REVIEW_DIMENSIONS,
        acceptance_focus=acceptance_focus,
    )


SCENARIOS: dict[str, KimiStyleBenchmarkScenario] = {
    "executive_memo_to_board_deck": _scenario(
        "executive_memo_to_board_deck",
        "Executive memo to board decision deck",
        ("uploaded_document", "intranet_document"),
        ("outline_to_approved_plan", "decision_storyline", "risk_guardrail_table", "render_based_visual_qa", "slide_level_citations"),
    ),
    "architecture_doc_to_architecture_review": _scenario(
        "architecture_doc_to_architecture_review",
        "Architecture document to architecture review deck",
        ("uploaded_document", "local_knowledge_base_entry"),
        ("topology_storyline", "component_responsibility_matrix", "failure_modes_operator_gates", "diagram_node_overlap_check", "architecture_claim_citations"),
    ),
    "project_log_to_status_deck": _scenario(
        "project_log_to_status_deck",
        "Project log to status review deck",
        ("uploaded_document", "generated_artifact_manifest"),
        ("latest_milestone_coverage", "timeline_native_visual", "risk_register", "next_actions_owner_table", "no_missing_late_milestones"),
    ),
    "comparison_table_to_decision_matrix": _scenario(
        "comparison_table_to_decision_matrix",
        "Comparison table to decision matrix deck",
        ("uploaded_document", "intranet_document"),
        ("native_option_matrix", "table_overflow_check", "explicit_recommendation", "source_row_citations", "no_raw_csv_as_narrative"),
    ),
    "long_doc_to_structured_explainer": _scenario(
        "long_doc_to_structured_explainer",
        "Long DOCX/PDF to structured explainer deck",
        ("uploaded_document", "local_knowledge_base_entry"),
        ("section_map", "evidence_package", "claim_guard", "no_filler_slides", "complete_source_ranges"),
    ),
    "research_report_to_cited_deck": _scenario(
        "research_report_to_cited_deck",
        "Research report to cited presentation",
        ("uploaded_document", "intranet_document"),
        ("research_claim_citations", "citation_manifest_coverage", "source_fragment_quality", "render_readability", "no_hidden_public_web_lookup"),
    ),
    "kpi_spreadsheet_to_business_review": _scenario(
        "kpi_spreadsheet_to_business_review",
        "KPI spreadsheet to business review deck",
        ("uploaded_document", "generated_artifact_manifest"),
        ("native_kpi_table_or_chart", "chart_label_collision_check", "data_series_citations", "executive_summary", "actionable_next_steps"),
    ),
    "product_launch_brief_to_launch_deck": _scenario(
        "product_launch_brief_to_launch_deck",
        "Product launch brief to launch deck",
        ("uploaded_document", "intranet_document"),
        ("launch_storyline", "audience_and_timing", "risk_or_dependency_table", "citation_backing", "operator_edit_loop_ready"),
    ),
    "training_material_to_training_deck": _scenario(
        "training_material_to_training_deck",
        "Training material to training deck",
        ("uploaded_document", "local_knowledge_base_entry"),
        ("learning_sequence", "section_map", "knowledge_check_or_recap", "visual_readability", "source_grounded_examples"),
    ),
    "screenshot_to_editable_slide": _scenario(
        "screenshot_to_editable_slide",
        "Screenshot or image to editable slide",
        ("image_region_evidence", "uploaded_document"),
        ("local_ocr_or_layout_metadata", "region_to_slide_element_provenance", "editable_pptx_reconstruction", "image_reconstruction_mismatch_check", "no_cloud_vision"),
    ),
    "branded_template_to_brand_deck": _scenario(
        "branded_template_to_brand_deck",
        "Local branded template to brand-consistent deck",
        ("uploaded_document", "generated_artifact_manifest"),
        ("local_template_master_metadata", "archetype_to_layout_mapping", "native_visual_layout_mapping", "brand_consistent_render", "external_template_discovery_forbidden"),
    ),
    "browser_evidence_packet_to_cited_deck": _scenario(
        "browser_evidence_packet_to_cited_deck",
        "Internal browser evidence packet to cited deck",
        ("internal_browser_evidence_packet", "intranet_document"),
        ("saved_evidence_packet_citations", "offline_boundary", "slide_claim_citation_coverage", "render_based_visual_qa", "no_live_public_web_dependency"),
    ),
}

ACCEPTANCE_POLICY = KimiStyleBenchmarkAcceptancePolicy(
    required_scenario_count=12,
    minimum_approved_scenario_count=10,
    rejects_allowed=0,
    blocker_defects_allowed=0,
    request_rework_allowed_for_parity_claim=0,
    minimum_citation_coverage=1.0,
    minimum_render_visual_qa_pass_rate=1.0,
    requires_completed_human_review=True,
    requires_render_based_visual_qa=True,
    requires_offline_intranet_source_boundary=True,
    requires_selected_parity_wording=True,
    accepted_final_claim_wording=ACCEPTED_FINAL_CLAIM_WORDING,
    whole_project_kimi_level_claim_allowed=False,
    generic_kimi_level_achieved_claim_allowed=False,
)


def validate_kimi_style_benchmark_registry(
    scenarios: dict[str, KimiStyleBenchmarkScenario] | None = None,
    policy: KimiStyleBenchmarkAcceptancePolicy = ACCEPTANCE_POLICY,
) -> list[str]:
    registry = scenarios or SCENARIOS
    errors: list[str] = []

    if len(registry) != policy.required_scenario_count:
        errors.append(f"expected {policy.required_scenario_count} S10 scenarios, got {len(registry)}")
    for scenario_id in S10_SCENARIO_IDS:
        if scenario_id not in registry:
            errors.append(f"missing S10 scenario: {scenario_id}")
    for scenario in registry.values():
        if scenario.scenario_id not in S10_SCENARIO_IDS:
            errors.append(f"unknown S10 scenario: {scenario.scenario_id}")
        if not scenario.offline_ready:
            errors.append(f"{scenario.scenario_id}: offline_ready must be true")
        if scenario.public_internet_required:
            errors.append(f"{scenario.scenario_id}: public internet must not be required")
        if scenario.cloud_vision_required:
            errors.append(f"{scenario.scenario_id}: cloud vision must not be required")
        for phase in REQUIRED_S_PHASE_EVIDENCE:
            if phase not in scenario.required_s_phase_evidence:
                errors.append(f"{scenario.scenario_id}: missing S-phase evidence {phase}")
        for output in REQUIRED_AUTOMATED_EVIDENCE:
            if output not in scenario.required_outputs:
                errors.append(f"{scenario.scenario_id}: missing required output {output}")
        for dimension in REQUIRED_HUMAN_REVIEW_DIMENSIONS:
            if dimension not in scenario.human_review_dimensions:
                errors.append(f"{scenario.scenario_id}: missing review dimension {dimension}")
        if len(scenario.acceptance_focus) < 5:
            errors.append(f"{scenario.scenario_id}: acceptance focus must contain at least five controls")

    if policy.minimum_approved_scenario_count < 10:
        errors.append("minimum approved scenario count must be at least 10")
    if policy.rejects_allowed != 0:
        errors.append("S10 parity claim policy must allow zero rejects")
    if policy.blocker_defects_allowed != 0:
        errors.append("S10 parity claim policy must allow zero blocker defects")
    if policy.request_rework_allowed_for_parity_claim != 0:
        errors.append("S10 selected parity claim must allow zero request_rework scenarios")
    if policy.minimum_citation_coverage < 1.0:
        errors.append("S10 citation coverage must be complete")
    if policy.minimum_render_visual_qa_pass_rate < 1.0:
        errors.append("S10 render visual QA pass rate must be complete")
    if not policy.requires_completed_human_review:
        errors.append("S10 must require completed human review")
    if not policy.requires_render_based_visual_qa:
        errors.append("S10 must require render-based visual QA")
    if not policy.requires_offline_intranet_source_boundary:
        errors.append("S10 must require offline/intranet source boundary")
    if not policy.requires_selected_parity_wording:
        errors.append("S10 must require selected parity wording")
    if policy.accepted_final_claim_wording != ACCEPTED_FINAL_CLAIM_WORDING:
        errors.append("S10 accepted final claim wording is incorrect")
    if policy.whole_project_kimi_level_claim_allowed:
        errors.append("S10 must not allow whole-project Kimi-level claims")
    if policy.generic_kimi_level_achieved_claim_allowed:
        errors.append("S10 must not allow generic Kimi-level achieved claims")
    return errors


def kimi_style_benchmark_report() -> dict[str, Any]:
    errors = validate_kimi_style_benchmark_registry()
    scenario_payload = {scenario_id: scenario.as_dict() for scenario_id, scenario in sorted(SCENARIOS.items())}
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S10_WORKFLOW_ID,
        "s_phase": "S10",
        "expanded_kimi_style_benchmark_completed_by_s10": not errors,
        "scenario_count": len(SCENARIOS),
        "required_scenario_count": ACCEPTANCE_POLICY.required_scenario_count,
        "scenario_ids": list(S10_SCENARIO_IDS),
        "required_s_phase_evidence_count": len(REQUIRED_S_PHASE_EVIDENCE),
        "required_s_phase_evidence": list(REQUIRED_S_PHASE_EVIDENCE),
        "required_automated_outputs": list(REQUIRED_AUTOMATED_EVIDENCE),
        "required_human_review_dimensions": list(REQUIRED_HUMAN_REVIEW_DIMENSIONS),
        "minimum_approved_scenario_count_for_selected_parity": ACCEPTANCE_POLICY.minimum_approved_scenario_count,
        "rejects_allowed_for_selected_parity": ACCEPTANCE_POLICY.rejects_allowed,
        "blocker_defects_allowed_for_selected_parity": ACCEPTANCE_POLICY.blocker_defects_allowed,
        "request_rework_allowed_for_selected_parity_claim": ACCEPTANCE_POLICY.request_rework_allowed_for_parity_claim,
        "completed_human_review_required_by_s10": ACCEPTANCE_POLICY.requires_completed_human_review,
        "render_based_visual_qa_required_by_s10": ACCEPTANCE_POLICY.requires_render_based_visual_qa,
        "citation_coverage_required_by_s10": ACCEPTANCE_POLICY.minimum_citation_coverage,
        "offline_intranet_source_boundary_required_by_s10": ACCEPTANCE_POLICY.requires_offline_intranet_source_boundary,
        "accepted_final_claim_wording_by_s10": ACCEPTANCE_POLICY.accepted_final_claim_wording,
        "selected_offline_workflow_parity_claim_supported_after_s10_benchmark": False,
        "selected_offline_workflow_parity_claim_requires_future_completed_results": True,
        "whole_project_kimi_level_supported": False,
        "kimi_level_claimed_by_s10": False,
        "generic_kimi_level_achieved_claim_allowed_by_s10": ACCEPTANCE_POLICY.generic_kimi_level_achieved_claim_allowed,
        "public_internet_required_by_s10": False,
        "hidden_public_internet_allowed_by_s10": False,
        "cloud_research_allowed_by_s10": False,
        "cloud_vision_allowed_by_s10": False,
        "server3_local_intranet_route_verified_by_s10": False,
        "api_endpoint_added_by_s10": False,
        "db_schema_migration_added_by_s10": False,
        "frontend_runtime_changed_by_s10": False,
        "dependency_versions_changed_by_s10": False,
        "dockerfiles_changed_by_s10": False,
        "next_recommended_step": "S10 review execution - generate benchmark packets and collect real completed human review before any selected parity claim.",
        "acceptance_policy": ACCEPTANCE_POLICY.as_dict(),
        "scenarios": scenario_payload,
        "errors": errors,
    }
