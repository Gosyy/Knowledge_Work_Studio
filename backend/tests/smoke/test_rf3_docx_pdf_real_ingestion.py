from __future__ import annotations

import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from backend.app.services.docx_service import DocxIngestionError, DocxService
from backend.app.services.docx_service.entrypoint import DocxIngestionRequest, DocxServiceEntrypoint
from backend.app.services.pdf_service import PdfImageOnlyError, PdfService
from backend.app.services.pdf_service.entrypoint import PdfIngestionRequest, PdfServiceEntrypoint


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sample_docx_bytes() -> bytes:
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Quarterly revenue increased.</w:t></w:r></w:p>
    <w:p><w:r><w:t>Customer retention stayed stable.</w:t></w:r></w:p>
    <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Table cell signal.</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
  </w:body>
</w:document>"""
    payload = BytesIO()
    with ZipFile(payload, "w", compression=ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", "<Types/>")
        docx.writestr("_rels/.rels", "<Relationships/>")
        docx.writestr("word/document.xml", document_xml)
    return payload.getvalue()


def sample_pdf_bytes() -> bytes:
    return b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /Contents 4 0 R >> endobj
4 0 obj << /Length 110 >> stream
BT /F1 12 Tf 72 720 Td (First PDF finding is stable.) Tj 0 -18 Td (Second finding needs review.) Tj ET
endstream endobj
%%EOF
"""


def image_only_pdf_bytes() -> bytes:
    return b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /Resources << /XObject << /Im1 4 0 R >> >> >> endobj
4 0 obj << /Type /XObject /Subtype /Image /Width 10 /Height 10 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length 3 >> stream
abc
endstream endobj
%%EOF
"""


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_docx_pdf_real_ingestion_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf3_checker_reports_ready_real_docx_pdf_ingestion() -> None:
    result = run_check("--require-ready", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "docx-pdf-real-ingestion-runtime"
    assert payload["checkpoint"] == "RF3"
    assert payload["status"] == "ready"
    assert payload["runtime_changed_by_rf3"] is True
    assert payload["dependency_versions_changed_by_rf3"] is False
    assert payload["dockerfiles_changed_by_rf3"] is False
    assert payload["api_endpoint_added_by_rf3"] is False
    assert payload["db_schema_migration_added_by_rf3"] is False
    assert payload["cloud_ocr_added_by_rf3"] is False
    assert payload["k_phase_started_by_rf3"] is False


def test_rf3_docx_service_extracts_real_docx_package_text() -> None:
    result = DocxService().ingest_docx(sample_docx_bytes(), source_filename="quarterly.docx")

    assert "Quarterly revenue increased." in result.extracted_text
    assert "Customer retention stayed stable." in result.extracted_text
    assert "Table cell signal." in result.extracted_text
    assert result.paragraph_count == 3
    assert result.table_cell_count == 1
    assert result.content_type.startswith("text/plain")
    assert result.artifact_content.startswith(b"DOCX Ingestion Report\n")
    assert result.safe_metadata["source_format"] == "docx"
    assert result.safe_metadata["network_required"] is False
    assert result.safe_metadata["fake_ocr_claimed"] is False


def test_rf3_pdf_service_extracts_text_layer_and_fails_honestly_for_image_only_pdf() -> None:
    service = PdfService()
    result = service.ingest_pdf(sample_pdf_bytes(), source_filename="findings.pdf", max_sentences=1)

    assert "First PDF finding is stable." in result.extracted_text
    assert "Second finding needs review." in result.extracted_text
    assert result.summary == "First PDF finding is stable."
    assert result.page_count == 1
    assert result.artifact_content.startswith(b"PDF Ingestion Report\n")
    assert result.safe_metadata["source_kind"] == "pdf_text_layer"
    assert result.safe_metadata["cloud_ocr_used"] is False
    assert result.safe_metadata["image_only_pdf_supported"] is False

    with pytest.raises(PdfImageOnlyError, match="OCR is not implemented in RF3"):
        service.ingest_pdf(image_only_pdf_bytes())


def test_rf3_entrypoints_expose_ingestion_without_public_api_or_schema_changes() -> None:
    docx_entrypoint = DocxServiceEntrypoint(service=DocxService())
    docx_result = docx_entrypoint.ingest(DocxIngestionRequest(content=sample_docx_bytes()))
    assert "Quarterly revenue" in docx_result.extracted_text
    assert docx_result.safe_metadata["runtime_changed_by_rf3"] is True

    pdf_entrypoint = PdfServiceEntrypoint(service=PdfService())
    pdf_result = pdf_entrypoint.ingest(PdfIngestionRequest(content=sample_pdf_bytes(), max_sentences=2))
    assert "Second finding needs review." in pdf_result.summary
    assert pdf_result.safe_metadata["runtime_changed_by_rf3"] is True


def test_rf3_rejects_malformed_docx_without_fake_success() -> None:
    with pytest.raises(DocxIngestionError, match="valid DOCX/ZIP"):
        DocxService().ingest_docx(b"not a docx")
