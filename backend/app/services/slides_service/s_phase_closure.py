from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.kimi_style_benchmark import (
    ACCEPTED_FINAL_CLAIM_WORDING,
    S10_SCENARIO_IDS,
    kimi_style_benchmark_report,
)

S11_WORKFLOW_ID = "slides.s_phase_closure"
CLOSED_S_PHASES = (
    "S1_gap_dossier",
    "S2_outline_first_frontend_workflow",
    "S3_adaptive_deck_modes",
    "S4_native_table_chart_diagram_rendering",
    "S5_template_master_ingestion",
    "S6_image_screenshot_to_slide_workflow",
    "S7_offline_intranet_research_citations",
    "S8_conversational_edit_loop",
    "S9_render_based_visual_qa",
    "S10_expanded_kimi_style_benchmark",
)

FORBIDDEN_CLAIMS = (
    "Kimi-level achieved",
    "whole-project Kimi-level parity",
    "generic Kimi Slides parity",
    "Server 3 local_intranet verified",
    "hidden public internet production dependency",
    "cloud research in default production runtime",
    "cloud vision in default production runtime",
)

FUTURE_SELECTED_PARITY_PREREQUISITES = (
    "execute_all_12_s10_scenarios",
    "collect_real_completed_human_review_results",
    "minimum_10_approved_scenarios",
    "zero_rejects",
    "zero_request_rework_for_selected_parity_claim",
    "zero_blocker_visual_defects",
    "citation_coverage_1_0",
    "render_based_visual_qa_evidence",
    "offline_intranet_source_boundary_preserved",
)


@dataclass(frozen=True)
class SPhaseClosureDossier:
    workflow_id: str
    title: str
    closed_s_phases: tuple[str, ...]
    accepted_future_claim_wording: str
    forbidden_claims: tuple[str, ...]
    future_selected_parity_prerequisites: tuple[str, ...]
    s10_scenario_count: int
    s_phase_capability_track_closed: bool
    selected_offline_workflow_parity_claim_supported_now: bool
    selected_offline_workflow_parity_claim_requires_future_completed_results: bool
    generic_kimi_level_achieved_claim_allowed: bool
    whole_project_kimi_level_supported: bool
    completed_human_review_fabricated_by_s11: bool
    server3_local_intranet_route_verified_by_s11: bool
    hidden_public_internet_allowed_by_s11: bool
    cloud_research_allowed_by_s11: bool
    cloud_vision_allowed_by_s11: bool
    offline_ready: bool
    provenance_required: bool

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["closed_s_phases"] = list(self.closed_s_phases)
        payload["forbidden_claims"] = list(self.forbidden_claims)
        payload["future_selected_parity_prerequisites"] = list(self.future_selected_parity_prerequisites)
        return payload


S_PHASE_CLOSURE_DOSSIER = SPhaseClosureDossier(
    workflow_id=S11_WORKFLOW_ID,
    title="S-phase closure dossier for Kimi Slides-class capability foundation",
    closed_s_phases=CLOSED_S_PHASES,
    accepted_future_claim_wording=ACCEPTED_FINAL_CLAIM_WORDING,
    forbidden_claims=FORBIDDEN_CLAIMS,
    future_selected_parity_prerequisites=FUTURE_SELECTED_PARITY_PREREQUISITES,
    s10_scenario_count=len(S10_SCENARIO_IDS),
    s_phase_capability_track_closed=True,
    selected_offline_workflow_parity_claim_supported_now=False,
    selected_offline_workflow_parity_claim_requires_future_completed_results=True,
    generic_kimi_level_achieved_claim_allowed=False,
    whole_project_kimi_level_supported=False,
    completed_human_review_fabricated_by_s11=False,
    server3_local_intranet_route_verified_by_s11=False,
    hidden_public_internet_allowed_by_s11=False,
    cloud_research_allowed_by_s11=False,
    cloud_vision_allowed_by_s11=False,
    offline_ready=True,
    provenance_required=True,
)


def validate_s_phase_closure_dossier(dossier: SPhaseClosureDossier = S_PHASE_CLOSURE_DOSSIER) -> list[str]:
    errors: list[str] = []
    s10 = kimi_style_benchmark_report()
    if dossier.workflow_id != S11_WORKFLOW_ID:
        errors.append("workflow_id must be slides.s_phase_closure")
    if len(dossier.closed_s_phases) != 10:
        errors.append("S11 must close exactly ten S-phase capability entries")
    for phase in CLOSED_S_PHASES:
        if phase not in dossier.closed_s_phases:
            errors.append(f"missing closed S-phase entry: {phase}")
    if s10.get("status") != "ready":
        errors.append("S11 requires S10 benchmark contract to be ready")
    if s10.get("scenario_count") != 12:
        errors.append("S11 requires the S10 12-scenario benchmark contract")
    if s10.get("selected_offline_workflow_parity_claim_supported_after_s10_benchmark") is not False:
        errors.append("S10 must not already support selected parity without completed results")
    if s10.get("selected_offline_workflow_parity_claim_requires_future_completed_results") is not True:
        errors.append("S10 must require future completed benchmark/human-review results")
    if dossier.accepted_future_claim_wording != ACCEPTED_FINAL_CLAIM_WORDING:
        errors.append("S11 accepted future claim wording must match S10")
    for claim in FORBIDDEN_CLAIMS:
        if claim not in dossier.forbidden_claims:
            errors.append(f"missing forbidden claim: {claim}")
    for prerequisite in FUTURE_SELECTED_PARITY_PREREQUISITES:
        if prerequisite not in dossier.future_selected_parity_prerequisites:
            errors.append(f"missing future selected parity prerequisite: {prerequisite}")
    must_be_true = {
        "s_phase_capability_track_closed": dossier.s_phase_capability_track_closed,
        "selected_offline_workflow_parity_claim_requires_future_completed_results": dossier.selected_offline_workflow_parity_claim_requires_future_completed_results,
        "offline_ready": dossier.offline_ready,
        "provenance_required": dossier.provenance_required,
    }
    for name, value in must_be_true.items():
        if value is not True:
            errors.append(f"{name} must be true")
    must_be_false = {
        "selected_offline_workflow_parity_claim_supported_now": dossier.selected_offline_workflow_parity_claim_supported_now,
        "generic_kimi_level_achieved_claim_allowed": dossier.generic_kimi_level_achieved_claim_allowed,
        "whole_project_kimi_level_supported": dossier.whole_project_kimi_level_supported,
        "completed_human_review_fabricated_by_s11": dossier.completed_human_review_fabricated_by_s11,
        "server3_local_intranet_route_verified_by_s11": dossier.server3_local_intranet_route_verified_by_s11,
        "hidden_public_internet_allowed_by_s11": dossier.hidden_public_internet_allowed_by_s11,
        "cloud_research_allowed_by_s11": dossier.cloud_research_allowed_by_s11,
        "cloud_vision_allowed_by_s11": dossier.cloud_vision_allowed_by_s11,
    }
    for name, value in must_be_false.items():
        if value is not False:
            errors.append(f"{name} must be false")
    return errors


def s_phase_closure_report() -> dict[str, Any]:
    dossier = S_PHASE_CLOSURE_DOSSIER
    errors = validate_s_phase_closure_dossier(dossier)
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S11_WORKFLOW_ID,
        "s_phase": "S11",
        "s_phase_closure_completed_by_s11": not errors,
        "s1_to_s10_capability_track_closed_by_s11": dossier.s_phase_capability_track_closed,
        "closed_s_phase_count": len(dossier.closed_s_phases),
        "closed_s_phases": list(dossier.closed_s_phases),
        "s10_scenario_count_confirmed_by_s11": dossier.s10_scenario_count,
        "accepted_future_claim_wording_by_s11": dossier.accepted_future_claim_wording,
        "selected_offline_workflow_parity_claim_supported_now_by_s11": dossier.selected_offline_workflow_parity_claim_supported_now,
        "selected_offline_workflow_parity_claim_requires_future_completed_results_by_s11": dossier.selected_offline_workflow_parity_claim_requires_future_completed_results,
        "future_selected_parity_prerequisites": list(dossier.future_selected_parity_prerequisites),
        "forbidden_claims": list(dossier.forbidden_claims),
        "generic_kimi_level_achieved_claim_allowed_by_s11": dossier.generic_kimi_level_achieved_claim_allowed,
        "kimi_level_claimed_by_s11": False,
        "whole_project_kimi_level_supported": dossier.whole_project_kimi_level_supported,
        "completed_human_review_fabricated_by_s11": dossier.completed_human_review_fabricated_by_s11,
        "server3_local_intranet_route_verified_by_s11": dossier.server3_local_intranet_route_verified_by_s11,
        "hidden_public_internet_allowed_by_s11": dossier.hidden_public_internet_allowed_by_s11,
        "cloud_research_allowed_by_s11": dossier.cloud_research_allowed_by_s11,
        "cloud_vision_allowed_by_s11": dossier.cloud_vision_allowed_by_s11,
        "public_internet_required_by_s11": False,
        "offline_ready_by_s11": dossier.offline_ready,
        "api_endpoint_added_by_s11": False,
        "db_schema_migration_added_by_s11": False,
        "frontend_runtime_changed_by_s11": False,
        "dependency_versions_changed_by_s11": False,
        "dockerfiles_changed_by_s11": False,
        "next_recommended_step": "Execute the S10 12-scenario benchmark and collect real completed human review results before any selected offline workflow parity claim.",
        "dossier": dossier.as_dict(),
        "errors": errors,
    }
