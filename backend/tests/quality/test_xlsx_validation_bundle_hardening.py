from __future__ import annotations

import json

from backend.app.services.xlsx_service import XlsxService, sample_xlsx_bytes
from backend.app.services.xlsx_service.validator import validate_xlsx_artifact_bundle


def test_kr5b_valid_xlsx_bundle_passes_manifest_and_traceability_validation() -> None:
    bundle = XlsxService().build_artifact_bundle(sample_xlsx_bytes(), source_filename="revenue_sample.xlsx")
    report = validate_xlsx_artifact_bundle(bundle)

    assert report.status == "ready", report.as_dict()["issues"]
    assert report.checks["required_artifacts_present"] is True
    assert report.checks["manifest_lists_required_artifacts"] is True
    assert report.checks["manifest_hashes_match"] is True
    assert report.checks["manifest_sizes_match"] is True
    assert report.checks["formula_inventory_traceable"] is True
    assert report.checks["preview_artifacts_traceable"] is True
    assert report.checks["quality_report_fail_closed"] is True


def test_kr5b_artifact_manifest_uses_explicit_self_reference_not_fake_hash() -> None:
    bundle = XlsxService().build_artifact_bundle(sample_xlsx_bytes(), source_filename="revenue_sample.xlsx")
    manifest = json.loads(bundle.text_artifact("artifact_manifest.json"))
    self_entries = [item for item in manifest["artifacts"] if item["path"] == "artifact_manifest.json"]

    assert len(self_entries) == 1
    assert self_entries[0]["self_reference"] is True
    assert self_entries[0]["sha256"] is None
    assert self_entries[0]["size_bytes"] is None


def test_kr5b_validation_fails_closed_when_manifest_hash_is_wrong() -> None:
    bundle = XlsxService().build_artifact_bundle(sample_xlsx_bytes(), source_filename="revenue_sample.xlsx")
    manifest = json.loads(bundle.text_artifact("artifact_manifest.json"))
    for item in manifest["artifacts"]:
        if item["path"] == "formula_inventory.json":
            item["sha256"] = "0" * 64
    bundle.artifacts["artifact_manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")

    report = validate_xlsx_artifact_bundle(bundle)
    assert report.status == "failed"
    assert any(issue.code == "manifest_hash_mismatch" for issue in report.issues)


def test_kr5b_validation_fails_closed_when_preview_is_missing() -> None:
    bundle = XlsxService().build_artifact_bundle(sample_xlsx_bytes(), source_filename="revenue_sample.xlsx")
    del bundle.artifacts["table_previews/Revenue.csv"]

    report = validate_xlsx_artifact_bundle(bundle)
    assert report.status == "failed"
    codes = {issue.code for issue in report.issues}
    assert "missing_required_artifact" in codes
    assert "missing_preview" in codes
