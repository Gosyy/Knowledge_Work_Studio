from __future__ import annotations

import json

from backend.app.services.xlsx_service import XlsxService, sample_xlsx_bytes
from backend.app.services.xlsx_service.entrypoint import XlsxInspectRequest, XlsxServiceEntrypoint


def test_kr5a_xlsx_service_inspects_sheet_metadata_and_formulas() -> None:
    result = XlsxService().inspect_workbook(sample_xlsx_bytes(), source_filename="revenue_sample.xlsx")

    assert result.status == "ready", result.errors
    assert result.workbook_opens is True
    assert result.sheet_count == 1
    assert result.sheets[0].sheet_name == "Revenue"
    assert result.sheets[0].used_range == "A1:B4"
    assert result.sheets[0].non_empty_cell_count == 8
    assert result.formula_count == 1
    assert result.formulas[0].cell_ref == "B4"
    assert result.formulas[0].formula == "SUM(B2:B3)"
    assert result.destructive_edit_performed is False
    assert len(result.source_sha256) == 64


def test_kr5a_xlsx_service_rejects_malformed_workbook_without_fake_success() -> None:
    result = XlsxService().inspect_workbook(b"not an xlsx", source_filename="broken.xlsx")

    assert result.status == "failed"
    assert result.workbook_opens is False
    assert result.sheet_count == 0
    assert result.errors
    assert result.destructive_edit_performed is False


def test_kr5a_xlsx_entrypoint_returns_downloadable_artifact_names() -> None:
    entrypoint = XlsxServiceEntrypoint(XlsxService())
    payload = entrypoint.inspect(XlsxInspectRequest(content=sample_xlsx_bytes(), source_filename="revenue_sample.xlsx"))

    assert payload.status == "ready"
    assert payload.workbook_opens is True
    assert "workbook_manifest.json" in payload.artifact_names
    assert "xlsx_analysis_report.json" in payload.artifact_names
    assert "formula_inventory.json" in payload.artifact_names
    assert "table_previews/Revenue.csv" in payload.artifact_names
    assert payload.analysis_report["source_kind"] == "xlsx"


def test_kr5a_csv_inspection_is_supported_as_excel_adjacent_input() -> None:
    csv_payload = b"Metric,Value\nRevenue Q1,100\nRevenue Q2,200\n"
    bundle = XlsxService().build_artifact_bundle(csv_payload, source_filename="revenue.csv")

    assert bundle.result.status == "ready", bundle.result.errors
    assert bundle.result.source_kind == "csv"
    assert bundle.result.sheet_count == 1
    assert "workbook.csv" in bundle.artifacts
    assert "table_previews/csv_input.csv" in bundle.artifacts
    quality = json.loads(bundle.text_artifact("quality_report.json"))
    assert quality["checks"]["workbook_opens"] is True
