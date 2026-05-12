from __future__ import annotations

import json
from pathlib import Path

from backend.app.services.slides_service.kq_deck_quality import (
    assess_kq1a_deck_artifact_bundle,
    build_kq1a_capabilities_report,
    create_kq1a_smoke_bundle,
    make_zip_from_dir,
    write_json,
)


def test_kq1a_accepts_complete_deck_artifact_bundle(tmp_path: Path) -> None:
    bundle = create_kq1a_smoke_bundle(tmp_path / "bundle", valid=True)

    result = assess_kq1a_deck_artifact_bundle(bundle)

    assert result.status == "ready", result.errors
    assert result.pptx_present is True
    assert result.pptx_valid_ooxml is True
    assert result.slide_count == 5
    assert result.rendered_slide_count == 5
    assert result.citation_count == 5
    assert result.source_evidence_count == 1
    assert result.geometry_report_present is True
    assert result.visual_qa_report_present is True
    assert result.review_packet_present is True
    assert result.review_packet_over_actual_deck is True
    assert result.screenshot_based_review_supported is True
    assert result.selected_offline_workflow_parity_claim_supported_after_kq1a is False
    assert result.kimi_level_claimed_by_kq1a is False
    assert result.server3_local_intranet_route_verified_by_kq1a is False
    assert result.controlled_scope["calls_gigachat_by_kq1a"] is False
    assert result.controlled_scope["generates_pptx_by_kq1a"] is False


def test_kq1a_accepts_complete_deck_artifact_zip(tmp_path: Path) -> None:
    bundle = create_kq1a_smoke_bundle(tmp_path / "bundle", valid=True)
    zip_path = tmp_path / "bundle.zip"
    make_zip_from_dir(bundle, zip_path)

    result = assess_kq1a_deck_artifact_bundle(zip_path)

    assert result.status == "ready", result.errors
    assert result.bundle_name == "bundle.zip"
    assert result.pptx_valid_ooxml is True
    assert result.rendered_slide_count == 5


def test_kq1a_rejects_json_only_bundle(tmp_path: Path) -> None:
    bundle = create_kq1a_smoke_bundle(tmp_path / "json_only", valid=False)

    result = assess_kq1a_deck_artifact_bundle(bundle)

    assert result.status == "failed"
    assert result.json_only_bundle_rejected is True
    assert any("JSON-only bundle rejected" in error for error in result.errors)
    assert result.pptx_present is False
    assert result.rendered_slide_count == 0


def test_kq1a_rejects_missing_rendered_screenshots(tmp_path: Path) -> None:
    bundle = create_kq1a_smoke_bundle(tmp_path / "bundle", valid=True)
    for image in (bundle / "rendered_slides").glob("*.png"):
        image.unlink()

    result = assess_kq1a_deck_artifact_bundle(bundle)

    assert result.status == "failed"
    assert any("rendered slide screenshot count" in error for error in result.errors)


def test_kq1a_rejects_prefilled_review_or_parity_claim(tmp_path: Path) -> None:
    bundle = create_kq1a_smoke_bundle(tmp_path / "bundle", valid=True)
    review_packet = bundle / "review_packet.json"
    payload = json.loads(review_packet.read_text(encoding="utf-8"))
    payload["human_review_decision"] = "approve"
    review_packet.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    write_json(bundle / "bad_claims.json", {"kimi_level_claimed": True})

    result = assess_kq1a_deck_artifact_bundle(bundle)

    assert result.status == "failed"
    assert any("human_review_decision" in error for error in result.errors)
    assert any("forbidden claim" in error for error in result.errors)


def test_kq1a_capabilities_keep_scope_controlled() -> None:
    report = build_kq1a_capabilities_report()

    assert report["deck_artifact_quality_harness_supported"] is True
    assert report["json_only_bundle_rejected"] is True
    assert report["requires_pptx"] is True
    assert report["requires_rendered_slide_screenshots"] is True
    assert report["requires_geometry_report"] is True
    assert report["requires_visual_qa_report"] is True
    assert report["requires_citation_manifest"] is True
    assert report["requires_source_evidence_manifest"] is True
    assert report["requires_review_packet_over_actual_deck"] is True
    assert report["api_endpoint_added_by_kq1a"] is False
    assert report["db_schema_migration_added_by_kq1a"] is False
    assert report["frontend_runtime_changed_by_kq1a"] is False
    assert report["dependency_versions_changed_by_kq1a"] is False
    assert report["dockerfiles_changed_by_kq1a"] is False
    assert report["calls_gigachat_by_kq1a"] is False
    assert report["reruns_model_generation_by_kq1a"] is False
    assert report["generates_pptx_by_kq1a"] is False
    assert report["kimi_level_claimed_by_kq1a"] is False
    assert report["whole_project_kimi_level_supported"] is False
