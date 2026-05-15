from __future__ import annotations

import zipfile
from pathlib import Path

from backend.app.services.slides_service.kq_deck_quality import assess_kq1a_deck_artifact_bundle, read_json
from backend.app.services.slides_service.kq_exec_memo_deck_generation import (
    KQ1B_CONTROLLED_SCOPE_FLAGS,
    build_exec_memo_slide_specs,
    generate_kq1b_exec_memo_deck_bundle,
)


def test_slides_exec_memo_workflow_generates_actual_pptx_artifact_bundle(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    bundle_zip = tmp_path / "slides-exec-memo-bundle.zip"
    report_dir = tmp_path / "quality-report"
    result = generate_kq1b_exec_memo_deck_bundle(bundle_dir, zip_out=bundle_zip, quality_report_dir=report_dir)
    assert result.status == "ready"
    assert result.kq1a_status == "ready"
    assert result.generates_actual_pptx is True
    assert result.human_review_state == "pending_human_review"
    assert bundle_zip.exists()
    assert (bundle_dir / "deck" / "executive_memo_to_board_deck.pptx").exists()
    assert (report_dir / "kq1a_deck_artifact_quality_report.json").exists()
    assessment = assess_kq1a_deck_artifact_bundle(bundle_zip)
    assert assessment.status == "ready"
    assert assessment.pptx_present is True
    assert assessment.review_packet_over_actual_deck is True


def test_slides_exec_memo_pptx_contains_native_slide_xml(tmp_path: Path) -> None:
    result = generate_kq1b_exec_memo_deck_bundle(tmp_path / "bundle")
    pptx_path = Path(result.pptx_path)
    with zipfile.ZipFile(pptx_path, "r") as archive:
        names = archive.namelist()
    assert "ppt/presentation.xml" in names
    slide_xml = [name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
    assert len(slide_xml) == result.slide_count


def test_slides_exec_memo_citation_manifest_grounds_every_slide(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    generate_kq1b_exec_memo_deck_bundle(bundle_dir)
    citations = read_json(bundle_dir / "citation_manifest.json")["citations"]
    slide_ids = {spec.slide_id for spec in build_exec_memo_slide_specs()}
    cited_slide_ids = {citation["slide_id"] for citation in citations}
    assert slide_ids == cited_slide_ids
    assert all(citation["source_id"] and citation["source_excerpt"] for citation in citations)


def test_slides_exec_memo_workflow_preserves_conservative_claim_boundaries(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    result = generate_kq1b_exec_memo_deck_bundle(bundle_dir)
    manifest = read_json(bundle_dir / "kq1b_generation_manifest.json")
    assert result.selected_offline_workflow_parity_claim_supported_after_kq1b is False
    assert result.kimi_level_claimed_by_kq1b is False
    assert result.server3_local_intranet_route_verified_by_kq1b is False
    assert result.independent_office_render_performed_by_kq1b is False
    assert manifest["visual_quality_requires_follow_up_independent_render"] is True
    for key, expected in KQ1B_CONTROLLED_SCOPE_FLAGS.items():
        assert manifest["controlled_scope"][key] is expected
