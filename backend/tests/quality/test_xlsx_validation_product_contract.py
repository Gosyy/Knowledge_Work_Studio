from __future__ import annotations

from scripts.kw_docx_pdf_xlsx_product_workflows_check import inspect_xlsx_bytes, sample_xlsx_bytes


def test_xlsx_validation_inventories_formulas_without_mutating_workbook() -> None:
    result = inspect_xlsx_bytes(sample_xlsx_bytes())

    assert result.status == "ready", result.errors
    assert result.formula_count == 1
    assert result.formula_refs == ("B4",)
    assert result.destructive_edit_performed is False


def test_xlsx_validation_reports_table_like_rows_and_cell_counts() -> None:
    result = inspect_xlsx_bytes(sample_xlsx_bytes())

    assert result.table_like_row_count == 4
    assert result.non_empty_cell_count == 8
    assert result.errors == ()
