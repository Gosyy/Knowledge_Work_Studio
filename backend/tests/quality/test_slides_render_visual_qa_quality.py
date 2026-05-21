from __future__ import annotations

import json

from backend.app.services.slides_service.render_visual_qa_bundle import sample_slides_render_visual_qa_bundle


def test_kr6b_quality_report_is_ready_and_fail_closed() -> None:
    bundle = sample_slides_render_visual_qa_bundle()
    quality = json.loads(bundle.text_artifact("visual_qa_report.json"))

    assert quality["status"] == "ready"
    assert quality["checks"]["source_grounded_bundle_ready"] is True
    assert quality["checks"]["render_artifact_count_matches_slides"] is True
    assert quality["checks"]["independent_render_artifact_count_matches_slides"] is True
    assert quality["checks"]["visual_qa_fail_closed"] is True
    assert quality["checks"]["no_unchecked_visual_claims"] is True


def test_kr6b_artifact_manifest_lists_render_and_visual_qa_outputs() -> None:
    bundle = sample_slides_render_visual_qa_bundle()
    manifest = json.loads(bundle.text_artifact("artifact_manifest.json"))
    manifest_paths = {record["path"] for record in manifest["artifacts"]}

    assert "render_manifest.json" in manifest_paths
    assert "geometry_report.json" in manifest_paths
    assert "visual_qa_report.json" in manifest_paths
    assert any(path.startswith("rendered_slides/") for path in manifest_paths)
    assert any(path.startswith("independent_rendered_slides/") for path in manifest_paths)


def test_kr6b_artifact_manifest_uses_self_reference_for_manifest_file() -> None:
    bundle = sample_slides_render_visual_qa_bundle()
    manifest = json.loads(bundle.text_artifact("artifact_manifest.json"))
    manifest_paths = {record["path"] for record in manifest["artifacts"]}

    assert manifest["self_reference"]["path"] == "artifact_manifest.json"
    assert "hash_policy" in manifest["self_reference"]
    assert "artifact_manifest.json" not in manifest_paths
    assert "render_manifest.json" in manifest_paths
    assert "visual_qa_report.json" in manifest_paths
