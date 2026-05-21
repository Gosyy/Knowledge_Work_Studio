from __future__ import annotations

import json

from backend.app.services.slides_service.source_grounded_continuation import (
    build_source_grounded_slides_bundle,
    sample_source_refs,
    sample_source_text,
)


def test_kr6a_quality_report_is_ready_and_fail_closed() -> None:
    ready_bundle = build_source_grounded_slides_bundle(source_text=sample_source_text(), source_refs=sample_source_refs())
    ready_quality = json.loads(ready_bundle.text_artifact("quality_report.json"))
    assert ready_quality["status"] == "ready"
    assert ready_quality["checks"]["all_slides_have_citations"] is True
    assert ready_quality["checks"]["citations_have_excerpts"] is True

    failed_bundle = build_source_grounded_slides_bundle(source_text=sample_source_text(), source_refs=())
    failed_quality = json.loads(failed_bundle.text_artifact("quality_report.json"))
    assert failed_quality["status"] == "not_ready"
    assert failed_quality["checks"]["source_refs_present"] is False


def test_kr6a_artifact_manifest_uses_explicit_self_reference() -> None:
    bundle = build_source_grounded_slides_bundle(source_text=sample_source_text(), source_refs=sample_source_refs())
    manifest = json.loads(bundle.text_artifact("artifact_manifest.json"))

    assert manifest["self_reference"]["path"] == "artifact_manifest.json"
    assert "hash is intentionally omitted" in manifest["self_reference"]["hash_policy"]
    assert {item["path"] for item in manifest["artifacts"]} >= set(bundle.artifact_names())
