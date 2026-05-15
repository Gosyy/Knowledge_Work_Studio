from __future__ import annotations

from backend.app.services.docx_service import DocxIngestionError, DocxService
from backend.app.services.docx_service.entrypoint import DocxIngestionRequest, DocxServiceEntrypoint
from scripts.kw_docx_pdf_xlsx_product_workflows_check import sample_docx_bytes


def test_docx_product_workflow_extracts_paragraphs_tables_and_metadata() -> None:
    result = DocxService().ingest_docx(sample_docx_bytes(), source_filename="product.docx")

    assert "Product DOCX workflow extracts paragraph text." in result.extracted_text
    assert "Product DOCX workflow preserves table signals." in result.extracted_text
    assert "DOCX table cell evidence." in result.extracted_text
    assert result.paragraph_count == 3
    assert result.table_cell_count == 1
    assert result.content_type.startswith("text/plain")
    assert result.artifact_content.startswith(b"DOCX Ingestion Report\n")
    assert result.safe_metadata["source_format"] == "docx"
    assert result.safe_metadata["network_required"] is False
    assert result.safe_metadata["fake_ocr_claimed"] is False


def test_docx_product_entrypoint_exposes_ingestion_without_public_api_or_schema_changes() -> None:
    entrypoint = DocxServiceEntrypoint(service=DocxService())
    result = entrypoint.ingest(DocxIngestionRequest(content=sample_docx_bytes(), source_filename="product.docx"))

    assert "Product DOCX workflow extracts paragraph text." in result.extracted_text
    assert result.safe_metadata["runtime_changed_by_rf3"] is True
    assert result.safe_metadata["network_required"] is False


def test_docx_product_workflow_rejects_malformed_docx_without_fake_success() -> None:
    try:
        DocxService().ingest_docx(b"not a docx package")
    except DocxIngestionError as exc:
        assert "valid DOCX/ZIP" in str(exc)
    else:
        raise AssertionError("malformed DOCX package unexpectedly succeeded")
