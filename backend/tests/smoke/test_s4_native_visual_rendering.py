from __future__ import annotations

from backend.app.services.slides_service.native_visuals import (
    NATIVE_VISUAL_TYPES,
    get_native_visual_specs,
    get_native_visual_specs_by_mode,
    native_visual_rendering_report,
    validate_native_visual_registry,
)


def test_s4_report_ready_and_preserves_boundaries() -> None:
    report = native_visual_rendering_report()
    assert report["status"] == "ready"
    assert report["native_table_chart_diagram_rendering_completed_by_s4"] is True
    assert report["native_visual_spec_count"] >= report["expected_minimum_native_visual_spec_count"]
    assert set(report["native_visual_types"]) == set(NATIVE_VISUAL_TYPES)
    assert report["kimi_level_claimed_by_s4"] is False
    assert report["server3_local_intranet_route_verified_by_s4"] is False
    assert report["public_internet_required_by_s4"] is False


def test_s4_covers_all_s3_deck_modes() -> None:
    grouped = get_native_visual_specs_by_mode()
    assert len(grouped) == 5
    assert all(grouped[mode_id] for mode_id in grouped)
    report = native_visual_rendering_report()
    assert report["deck_mode_count_with_native_visuals"] == report["expected_deck_mode_count"]


def test_s4_decision_matrix_and_architecture_visuals_are_native() -> None:
    specs = {spec.visual_id: spec for spec in get_native_visual_specs()}
    assert specs["decision_option_matrix"].visual_type == "pptx_table"
    assert specs["decision_option_matrix"].native_pptx_element == "table"
    assert specs["architecture_topology_diagram"].visual_type == "pptx_diagram"
    assert specs["architecture_topology_diagram"].native_pptx_element == "shape_diagram"
    assert specs["architecture_failure_gate_table"].visual_type == "pptx_table"


def test_s4_native_visuals_are_editable_offline_and_provenance_bound() -> None:
    specs = get_native_visual_specs()
    assert not validate_native_visual_registry(specs)
    assert all(spec.editable_in_powerpoint for spec in specs)
    assert all(spec.raster_fallback_allowed is False for spec in specs)
    assert all(spec.offline_ready for spec in specs)
    assert all(spec.public_internet_required is False for spec in specs)
    assert all(spec.browser_required is False for spec in specs)
    assert all(spec.provenance_policy.strip() for spec in specs)
    assert all(spec.layout_guard.strip() for spec in specs)
