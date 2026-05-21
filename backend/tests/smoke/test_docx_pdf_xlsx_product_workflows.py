from __future__ import annotations

from pathlib import Path

from scripts.kw_docx_pdf_xlsx_product_workflows_check import build_report


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_kr2f_docx_pdf_xlsx_product_workflows_are_ready() -> None:
    report = build_report(REPO_ROOT)

    assert report["status"] == "ready"
    assert report["summary"]["product_tests_ready"] == report["summary"]["product_tests_required"]
    assert report["summary"]["product_docs_ready"] == report["summary"]["product_docs_checked"]
    assert report["summary"]["xlsx_workbook_opens"] is True
    assert report["summary"]["xlsx_formula_inventory_supported"] is True
    assert report["summary"]["physical_docs_codex_archive_allowed"] is False
    assert report["issues"] == []
