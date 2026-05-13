from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

MANDATORY_WORKFLOW_DOCS = {
    "docx": "docs/workflows/DOCX_WORKFLOW.md",
    "pdf": "docs/workflows/PDF_WORKFLOW.md",
    "xlsx": "docs/workflows/XLSX_WORKFLOW.md",
    "slides": "docs/workflows/SLIDES_WORKFLOW.md",
    "python_analysis": "docs/workflows/PYTHON_ANALYSIS_WORKFLOW.md",
    "browser_evidence": "docs/workflows/BROWSER_EVIDENCE_WORKFLOW.md",
}

LEGACY_WORKFLOW_BRIDGES = {
    "docx_pdf_ingestion": "scripts/kw_docx_pdf_real_ingestion_check.py",
    "slides_plan_first": "scripts/kw_slides_plan_first_check.py",
    "slides_artifact_quality": "scripts/kw_kq1_deck_quality_check.py",
    "python_analysis_contract": "docs/workflows/PYTHON_ANALYSIS_WORKFLOW.md",
    "browser_evidence_contract": "scripts/kw_browser_evidence_capture_check.py",
}


def test_mandatory_product_workflow_docs_exist() -> None:
    missing = [path for path in MANDATORY_WORKFLOW_DOCS.values() if not (REPO_ROOT / path).exists()]
    assert missing == []


def test_product_workflow_aliases_have_current_legacy_bridges() -> None:
    missing = [path for path in LEGACY_WORKFLOW_BRIDGES.values() if not (REPO_ROOT / path).exists()]
    assert missing == []


def test_xlsx_is_first_class_scope_even_before_runtime_implementation() -> None:
    workflow_doc = REPO_ROOT / "docs/workflows/XLSX_WORKFLOW.md"
    validation_doc = REPO_ROOT / "docs/quality/XLSX_VALIDATION.md"

    assert workflow_doc.exists()
    assert validation_doc.exists()
    combined = workflow_doc.read_text(encoding="utf-8") + "\n" + validation_doc.read_text(encoding="utf-8")
    for required_term in ("workbook", "formula", "validation", "artifact"):
        assert required_term.lower() in combined.lower()
