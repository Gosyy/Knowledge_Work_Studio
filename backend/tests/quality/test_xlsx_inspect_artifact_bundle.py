from __future__ import annotations

import json

from backend.app.services.xlsx_service import XlsxService, sample_xlsx_bytes


def test_kr5a_xlsx_bundle_contains_required_artifacts_and_manifests() -> None:
    bundle = XlsxService().build_artifact_bundle(sample_xlsx_bytes(), source_filename="revenue_sample.xlsx")
    artifact_names = set(bundle.artifact_names())

    assert {
        "workbook.xlsx",
        "workbook_manifest.json",
        "xlsx_analysis_report.json",
        "formula_inventory.json",
        "table_previews/Revenue.csv",
        "source_evidence_manifest.json",
        "artifact_manifest.json",
        "quality_report.json",
    }.issubset(artifact_names)

    manifest = json.loads(bundle.text_artifact("artifact_manifest.json"))
    manifest_paths = {item["path"] for item in manifest["artifacts"]}
    assert "table_previews/Revenue.csv" in manifest_paths
    assert "formula_inventory.json" in manifest_paths


def test_kr5a_xlsx_quality_report_is_fail_closed_and_non_destructive() -> None:
    bundle = XlsxService().build_artifact_bundle(sample_xlsx_bytes(), source_filename="revenue_sample.xlsx")
    quality = json.loads(bundle.text_artifact("quality_report.json"))

    assert quality["status"] == "ready"
    assert quality["checks"]["workbook_opens"] is True
    assert quality["checks"]["sheet_metadata_extracted"] is True
    assert quality["checks"]["formula_inventory_written"] is True
    assert quality["checks"]["table_previews_written"] is True
    assert quality["checks"]["destructive_edit_performed"] is False
    assert quality["checks"]["source_hash_recorded"] is True


def test_kr5a_xlsx_source_evidence_tracks_sheet_range_to_preview() -> None:
    bundle = XlsxService().build_artifact_bundle(sample_xlsx_bytes(), source_filename="revenue_sample.xlsx")
    evidence = json.loads(bundle.text_artifact("source_evidence_manifest.json"))

    assert evidence["evidence_items"]
    item = evidence["evidence_items"][0]
    assert item["source_range"] == "A1:B4"
    assert item["preview_artifact"] == "table_previews/Revenue.csv"
    assert item["worksheet_file"] == "xl/worksheets/sheet1.xml"
