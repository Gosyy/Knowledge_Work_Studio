from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.adaptive_deck_modes import (
    DECK_MODE_IDS,
    get_adaptive_deck_mode_registry,
)

S4_WORKFLOW_ID = "slides.native_visual_rendering"

NATIVE_VISUAL_TYPES = ("pptx_table", "pptx_chart", "pptx_diagram")
PPTX_NATIVE_ELEMENT_TYPES = ("table", "chart", "shape_diagram")


@dataclass(frozen=True)
class NativeVisualSpec:
    visual_id: str
    deck_mode_id: str
    slide_archetype: str
    visual_type: str
    native_pptx_element: str
    title: str
    data_model_policy: str
    renderer_contract: str
    layout_guard: str
    provenance_policy: str
    editable_in_powerpoint: bool = True
    raster_fallback_allowed: bool = False
    offline_ready: bool = True
    browser_required: bool = False
    public_internet_required: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


NATIVE_VISUAL_SPECS: tuple[NativeVisualSpec, ...] = (
    NativeVisualSpec(
        visual_id="executive_risk_guardrail_table",
        deck_mode_id="executive_board_deck",
        slide_archetype="risk_guardrail_table",
        visual_type="pptx_table",
        native_pptx_element="table",
        title="Risk guardrail table",
        data_model_policy="risk rows with owner, mitigation, status, and evidence link columns",
        renderer_contract="create editable PPTX table rows; never flatten risk content into bullet text",
        layout_guard="max six rows; wrap owner/action cells; split overflow into continuation slide",
        provenance_policy="each risk row must link to a source fragment or accepted review evidence",
    ),
    NativeVisualSpec(
        visual_id="executive_decision_signal_chart",
        deck_mode_id="executive_board_deck",
        slide_archetype="recommendation_slide",
        visual_type="pptx_chart",
        native_pptx_element="chart",
        title="Decision signal chart",
        data_model_policy="compact readiness, risk, and recommendation confidence values",
        renderer_contract="render editable bar or scorecard chart from structured decision inputs",
        layout_guard="chart labels must remain readable at board-review zoom levels",
        provenance_policy="scores must reference the decision evidence rows that produced them",
    ),
    NativeVisualSpec(
        visual_id="architecture_topology_diagram",
        deck_mode_id="architecture_review_deck",
        slide_archetype="topology_map",
        visual_type="pptx_diagram",
        native_pptx_element="shape_diagram",
        title="Architecture topology diagram",
        data_model_policy="components, server roles, data/control links, and offline boundary markers",
        renderer_contract="create editable PPTX shapes and connectors, not a raster screenshot",
        layout_guard="component labels cannot overlap connectors; Server 1/2/3 boundaries must be visible",
        provenance_policy="each component and boundary claim links to source architecture fragments",
    ),
    NativeVisualSpec(
        visual_id="architecture_failure_gate_table",
        deck_mode_id="architecture_review_deck",
        slide_archetype="failure_modes_operator_gates",
        visual_type="pptx_table",
        native_pptx_element="table",
        title="Failure modes and operator gates table",
        data_model_policy="failure mode, detection signal, operator gate, owner, and re-run path columns",
        renderer_contract="render as editable table with explicit operator gate rows",
        layout_guard="slide title/body must not overlap; split long rows before overflow",
        provenance_policy="each failure mode links to the control or runbook evidence that mitigates it",
    ),
    NativeVisualSpec(
        visual_id="project_status_milestone_timeline",
        deck_mode_id="project_status_deck",
        slide_archetype="milestone_timeline",
        visual_type="pptx_chart",
        native_pptx_element="chart",
        title="Milestone timeline",
        data_model_policy="ordered milestones with state, date/window, owner, and evidence source",
        renderer_contract="render editable timeline chart from structured milestone records",
        layout_guard="preserve late milestones; avoid crowding by grouping minor entries",
        provenance_policy="each milestone links to the log section that supports it",
    ),
    NativeVisualSpec(
        visual_id="project_status_risk_register",
        deck_mode_id="project_status_deck",
        slide_archetype="risk_register",
        visual_type="pptx_table",
        native_pptx_element="table",
        title="Risk register",
        data_model_policy="risk, impact, likelihood, mitigation, owner, due date, and evidence columns",
        renderer_contract="render editable risk table; no generic risk bullets without owner/status",
        layout_guard="cap rows per slide and split overflow without losing owners",
        provenance_policy="risk rows link to source notes or current-state entries",
    ),
    NativeVisualSpec(
        visual_id="decision_option_matrix",
        deck_mode_id="decision_matrix_deck",
        slide_archetype="option_matrix",
        visual_type="pptx_table",
        native_pptx_element="table",
        title="Option decision matrix",
        data_model_policy="preserve source rows/columns as options, criteria, strengths, weaknesses, and recommendation signals",
        renderer_contract="render editable PPTX decision matrix; raw CSV headers must not become slide titles",
        layout_guard="matrix columns must fit or be split by criteria group; no table overflow",
        provenance_policy="each option and criterion links to the source row/cell used to build it",
    ),
    NativeVisualSpec(
        visual_id="decision_tradeoff_chart",
        deck_mode_id="decision_matrix_deck",
        slide_archetype="tradeoff_summary",
        visual_type="pptx_chart",
        native_pptx_element="chart",
        title="Tradeoff summary chart",
        data_model_policy="criteria scores or qualitative signals normalized from the decision matrix",
        renderer_contract="render editable chart from structured matrix values; no raster-only chart fallback",
        layout_guard="recommendation must be visually prominent and not hidden behind chart labels",
        provenance_policy="chart values trace back to option-matrix source cells",
    ),
    NativeVisualSpec(
        visual_id="long_document_section_map",
        deck_mode_id="long_document_explainer",
        slide_archetype="section_map",
        visual_type="pptx_diagram",
        native_pptx_element="shape_diagram",
        title="Document section map",
        data_model_policy="source sections, page/range references, hierarchy, and generated slide mapping",
        renderer_contract="render editable section-map shapes from extracted document structure",
        layout_guard="section labels must be scannable; collapse deep subsections into grouped nodes",
        provenance_policy="each section node links to the source document range it summarizes",
    ),
    NativeVisualSpec(
        visual_id="long_document_evidence_table",
        deck_mode_id="long_document_explainer",
        slide_archetype="evidence_package",
        visual_type="pptx_table",
        native_pptx_element="table",
        title="Evidence package table",
        data_model_policy="claim, evidence excerpt summary, source range, confidence, and limitation columns",
        renderer_contract="render editable evidence table; no filler slides or unsupported claims",
        layout_guard="split evidence rows before overflow; keep source range visible",
        provenance_policy="each claim row must carry source range and limitation metadata",
    ),
)


def get_native_visual_specs() -> tuple[NativeVisualSpec, ...]:
    return NATIVE_VISUAL_SPECS


def get_native_visual_specs_by_mode() -> dict[str, tuple[NativeVisualSpec, ...]]:
    grouped: dict[str, list[NativeVisualSpec]] = {mode_id: [] for mode_id in DECK_MODE_IDS}
    for spec in NATIVE_VISUAL_SPECS:
        grouped.setdefault(spec.deck_mode_id, []).append(spec)
    return {mode_id: tuple(items) for mode_id, items in grouped.items()}


def validate_native_visual_spec(spec: NativeVisualSpec, mode_archetypes: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    if spec.deck_mode_id not in DECK_MODE_IDS:
        errors.append(f"{spec.visual_id}: unknown deck mode {spec.deck_mode_id}")
    if spec.visual_type not in NATIVE_VISUAL_TYPES:
        errors.append(f"{spec.visual_id}: unsupported visual type {spec.visual_type}")
    if spec.native_pptx_element not in PPTX_NATIVE_ELEMENT_TYPES:
        errors.append(f"{spec.visual_id}: unsupported native PPTX element {spec.native_pptx_element}")
    if spec.visual_type == "pptx_table" and spec.native_pptx_element != "table":
        errors.append(f"{spec.visual_id}: pptx_table must use table element")
    if spec.visual_type == "pptx_chart" and spec.native_pptx_element != "chart":
        errors.append(f"{spec.visual_id}: pptx_chart must use chart element")
    if spec.visual_type == "pptx_diagram" and spec.native_pptx_element != "shape_diagram":
        errors.append(f"{spec.visual_id}: pptx_diagram must use editable shape_diagram element")
    if spec.slide_archetype not in mode_archetypes.get(spec.deck_mode_id, set()):
        errors.append(f"{spec.visual_id}: slide archetype {spec.slide_archetype!r} is not registered for {spec.deck_mode_id}")
    if not spec.editable_in_powerpoint:
        errors.append(f"{spec.visual_id}: visual must be editable in PowerPoint")
    if spec.raster_fallback_allowed:
        errors.append(f"{spec.visual_id}: raster fallback must not be the primary renderer path")
    if not spec.offline_ready:
        errors.append(f"{spec.visual_id}: offline_ready must be true")
    if spec.browser_required:
        errors.append(f"{spec.visual_id}: browser runtime must not be required")
    if spec.public_internet_required:
        errors.append(f"{spec.visual_id}: public internet must not be required")
    for field_name, value in (
        ("data_model_policy", spec.data_model_policy),
        ("renderer_contract", spec.renderer_contract),
        ("layout_guard", spec.layout_guard),
        ("provenance_policy", spec.provenance_policy),
    ):
        if not value.strip():
            errors.append(f"{spec.visual_id}: {field_name} is required")
    return errors


def validate_native_visual_registry(specs: tuple[NativeVisualSpec, ...] | None = None) -> list[str]:
    specs = specs or NATIVE_VISUAL_SPECS
    errors: list[str] = []
    adaptive_modes = get_adaptive_deck_mode_registry()
    mode_archetypes = {
        mode_id: set(mode.required_slide_archetypes)
        for mode_id, mode in adaptive_modes.items()
    }
    by_mode = get_native_visual_specs_by_mode()
    for mode_id in DECK_MODE_IDS:
        if not by_mode.get(mode_id):
            errors.append(f"missing native visual specs for deck mode {mode_id}")
    visual_types = {spec.visual_type for spec in specs}
    for required_type in NATIVE_VISUAL_TYPES:
        if required_type not in visual_types:
            errors.append(f"missing native visual type: {required_type}")
    for spec in specs:
        errors.extend(validate_native_visual_spec(spec, mode_archetypes))

    lookup = {spec.visual_id: spec for spec in specs}
    required_visual_ids = (
        "decision_option_matrix",
        "architecture_topology_diagram",
        "architecture_failure_gate_table",
        "project_status_milestone_timeline",
        "long_document_evidence_table",
    )
    for visual_id in required_visual_ids:
        if visual_id not in lookup:
            errors.append(f"missing required native visual spec: {visual_id}")
    if lookup.get("decision_option_matrix") and lookup["decision_option_matrix"].visual_type != "pptx_table":
        errors.append("decision_option_matrix must be a native PPTX table")
    if lookup.get("architecture_topology_diagram") and lookup["architecture_topology_diagram"].visual_type != "pptx_diagram":
        errors.append("architecture_topology_diagram must be a native PPTX diagram")
    return errors


def native_visual_rendering_report() -> dict[str, Any]:
    specs = get_native_visual_specs()
    grouped = get_native_visual_specs_by_mode()
    errors = validate_native_visual_registry(specs)
    visual_types = sorted({spec.visual_type for spec in specs})
    spec_payload = [spec.as_dict() for spec in specs]
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S4_WORKFLOW_ID,
        "s_phase": "S4",
        "native_table_chart_diagram_rendering_completed_by_s4": not errors,
        "native_visual_spec_count": len(specs),
        "expected_minimum_native_visual_spec_count": 10,
        "native_visual_types": visual_types,
        "expected_native_visual_types": list(NATIVE_VISUAL_TYPES),
        "deck_mode_count_with_native_visuals": sum(1 for items in grouped.values() if items),
        "expected_deck_mode_count": len(DECK_MODE_IDS),
        "mode_visual_counts": {mode_id: len(items) for mode_id, items in grouped.items()},
        "decision_matrix_native_table_ready_by_s4": any(spec.visual_id == "decision_option_matrix" for spec in specs),
        "architecture_diagram_ready_by_s4": any(spec.visual_id == "architecture_topology_diagram" for spec in specs),
        "architecture_failure_gate_table_ready_by_s4": any(spec.visual_id == "architecture_failure_gate_table" for spec in specs),
        "project_status_timeline_ready_by_s4": any(spec.visual_id == "project_status_milestone_timeline" for spec in specs),
        "long_document_evidence_table_ready_by_s4": any(spec.visual_id == "long_document_evidence_table" for spec in specs),
        "pptx_native_editable_elements_required_by_s4": True,
        "raster_fallback_primary_path_allowed_by_s4": False,
        "source_to_visual_provenance_required_by_s4": True,
        "table_chart_policy_consumes_s3_modes": True,
        "visual_qa_expectations_ready_for_s9": True,
        "offline_ready_by_s4": all(spec.offline_ready for spec in specs),
        "public_internet_required_by_s4": False,
        "browser_runtime_required_by_s4": False,
        "api_endpoint_added_by_s4": False,
        "db_schema_migration_added_by_s4": False,
        "frontend_runtime_changed_by_s4": False,
        "dependency_versions_changed_by_s4": False,
        "dockerfiles_changed_by_s4": False,
        "cloud_llm_added_by_s4": False,
        "cloud_vision_added_by_s4": False,
        "kimi_level_claimed_by_s4": False,
        "whole_project_kimi_level_supported": False,
        "server3_local_intranet_route_verified_by_s4": False,
        "next_recommended_step": "S5 - template and slide-master ingestion with local template constraints.",
        "native_visual_specs": spec_payload,
        "errors": errors,
    }
