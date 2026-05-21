from __future__ import annotations

import json
from pathlib import Path

from backend.app.services.slides_service.kq_deck_quality import (
    assess_kq1a_deck_artifact_bundle,
    create_kq1a_smoke_bundle,
    make_zip_from_dir,
    write_json,
)


def test_slides_artifact_bundle_requires_real_pptx_rendered_slides_and_review_packet(tmp_path: Path) -> None:
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


def test_slides_artifact_bundle_rejects_json_only_output(tmp_path: Path) -> None:
    bundle = create_kq1a_smoke_bundle(tmp_path / "json_only", valid=False)
    result = assess_kq1a_deck_artifact_bundle(bundle)
    assert result.status == "failed"
    assert result.json_only_bundle_rejected is True
    assert result.pptx_present is False
    assert any("JSON-only bundle rejected" in error for error in result.errors)


def test_slides_artifact_bundle_zip_preserves_quality_contract(tmp_path: Path) -> None:
    bundle = create_kq1a_smoke_bundle(tmp_path / "bundle", valid=True)
    zip_path = tmp_path / "bundle.zip"
    make_zip_from_dir(bundle, zip_path)
    result = assess_kq1a_deck_artifact_bundle(zip_path)
    assert result.status == "ready", result.errors
    assert result.bundle_name == "bundle.zip"
    assert result.pptx_valid_ooxml is True
    assert result.rendered_slide_count == result.slide_count


def test_slides_artifact_bundle_rejects_prefilled_human_review_or_kimi_claim(tmp_path: Path) -> None:
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
