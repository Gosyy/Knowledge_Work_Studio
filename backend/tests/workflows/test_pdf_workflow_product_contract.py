from __future__ import annotations

import pytest

from backend.app.services.pdf_service import PdfImageOnlyError, PdfService
from backend.app.services.pdf_service.entrypoint import PdfIngestionRequest, PdfServiceEntrypoint
from scripts.kw_docx_pdf_xlsx_product_workflows_check import image_only_pdf_bytes, sample_pdf_bytes


def test_pdf_product_workflow_extracts_text_layer_and_summary_without_cloud_ocr() -> None:
    result = PdfService().ingest_pdf(sample_pdf_bytes(), source_filename="product.pdf", max_sentences=1)

    assert "Product PDF workflow extracts text layer." in result.extracted_text
    assert "Second PDF sentence remains available." in result.extracted_text
    assert result.summary == "Product PDF workflow extracts text layer."
    assert result.page_count == 1
    assert result.artifact_content.startswith(b"PDF Ingestion Report\n")
    assert result.safe_metadata["source_kind"] == "pdf_text_layer"
    assert result.safe_metadata["cloud_ocr_used"] is False
    assert result.safe_metadata["image_only_pdf_supported"] is False


def test_pdf_product_entrypoint_exposes_ingestion_without_public_api_or_schema_changes() -> None:
    entrypoint = PdfServiceEntrypoint(service=PdfService())
    result = entrypoint.ingest(
        PdfIngestionRequest(content=sample_pdf_bytes(), source_filename="product.pdf", max_sentences=2)
    )

    assert "Second PDF sentence remains available." in result.summary
    assert result.safe_metadata["runtime_changed_by_rf3"] is True
    assert result.safe_metadata["cloud_ocr_used"] is False


def test_pdf_product_workflow_fails_honestly_for_image_only_pdf_until_ocr_exists() -> None:
    with pytest.raises(PdfImageOnlyError, match="OCR is not implemented"):
        PdfService().ingest_pdf(image_only_pdf_bytes(), source_filename="image-only.pdf")
