from __future__ import annotations

from backend.app.services.slides_service.render_based_visual_qa import (
    REQUIRED_RENDER_EVIDENCE,
    REQUIRED_VISUAL_CHECKS,
    render_based_visual_qa_report,
    validate_render_based_visual_qa_contract,
)


def test_s9_render_based_visual_qa_contract_ready() -> None:
    report = render_based_visual_qa_report()
    assert report["status"] == "ready"
    assert report["render_based_visual_qa_completed_by_s9"] is True
    assert report["actual_slide_render_required_by_s9"] is True
    assert report["geometry_manifest_required_by_s9"] is True
    assert report["slide_level_defect_report_required_by_s9"] is True


def test_s9_required_visual_checks_cover_known_failure_modes() -> None:
    checks = set(REQUIRED_VISUAL_CHECKS)
    assert "title_body_collision" in checks
    assert "text_box_overlap" in checks
    assert "clipped_text" in checks
    assert "tiny_text" in checks
    assert "table_overflow" in checks
    assert "diagram_node_overlap" in checks
    assert "citation_marker_visibility" in checks


def test_s9_render_evidence_links_s4_s6_s7_s8() -> None:
    evidence = set(REQUIRED_RENDER_EVIDENCE)
    assert "rendered_slide_screenshot" in evidence
    assert "native_visual_geometry_manifest" in evidence
    assert "image_region_reconstruction_manifest" in evidence
    assert "citation_manifest" in evidence
    assert "revised_plan_snapshot_metadata" in evidence


def test_s9_boundaries_are_offline_and_no_false_claims() -> None:
    report = render_based_visual_qa_report()
    assert report["cloud_vision_allowed_by_s9"] is False
    assert report["hidden_public_internet_allowed_by_s9"] is False
    assert report["public_internet_required_by_s9"] is False
    assert report["visual_qa_score_alone_can_approve_by_s9"] is False
    assert report["semantic_qa_alone_can_approve_by_s9"] is False
    assert report["kimi_level_claimed_by_s9"] is False
    assert report["server3_local_intranet_route_verified_by_s9"] is False
    assert validate_render_based_visual_qa_contract() == []
