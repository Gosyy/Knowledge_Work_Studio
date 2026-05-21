from __future__ import annotations

from scripts.kw_docx_pdf_xlsx_product_workflows_check import inspect_xlsx_bytes, sample_xlsx_bytes


def test_xlsx_product_workflow_opens_workbook_and_reports_sheet_metadata() -> None:
    result = inspect_xlsx_bytes(sample_xlsx_bytes())

    assert result.status == "ready", result.errors
    assert result.workbook_opens is True
    assert result.sheet_count == 1
    assert result.sheet_names == ("Revenue",)
    assert result.worksheet_files == ("xl/worksheets/sheet1.xml",)
    assert result.non_empty_cell_count >= 8
    assert result.table_like_row_count >= 4


def test_xlsx_product_workflow_rejects_malformed_workbook_without_fake_success() -> None:
    result = inspect_xlsx_bytes(b"not an xlsx")

    assert result.status == "failed"
    assert result.workbook_opens is False
    assert result.errors
    assert result.destructive_edit_performed is False
