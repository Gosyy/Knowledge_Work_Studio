from __future__ import annotations

from scripts.kw_product_docs_check import REQUIRED_DOCS, build_report


def test_product_documentation_skeleton_is_ready() -> None:
    report = build_report(__import__("pathlib").Path(__file__).resolve().parents[3])
    assert report["status"] == "ready", report["issues"]
    assert report["missing_doc_count"] == 0
    assert report["required_doc_count"] == len(REQUIRED_DOCS)


def test_product_documentation_includes_xlsx_as_first_class_workflow() -> None:
    report = build_report(__import__("pathlib").Path(__file__).resolve().parents[3])
    assert "XLSX" in report["mandatory_workflows"]
    assert "XLSX" not in report["missing_workflows"]
