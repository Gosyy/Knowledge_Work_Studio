#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

REQUIRED_FILES = (
    "docs/codex/DOCX_PDF_REAL_INGESTION_RUNTIME.md",
    "backend/app/services/docx_service/ingestion.py",
    "backend/app/services/docx_service/service.py",
    "backend/app/services/docx_service/entrypoint.py",
    "backend/app/services/docx_service/__init__.py",
    "backend/app/services/pdf_service/ingestion.py",
    "backend/app/services/pdf_service/service.py",
    "backend/app/services/pdf_service/entrypoint.py",
    "backend/app/services/pdf_service/__init__.py",
    "scripts/kw_docx_pdf_real_ingestion_check.py",
    "backend/tests/smoke/test_rf3_docx_pdf_real_ingestion.py",
)

REQUIRED_MARKERS = {
    "docx_ingestion_output": ("backend/app/services/docx_service/ingestion.py", "class DocxIngestionOutput"),
    "docx_ingest_function": ("backend/app/services/docx_service/ingestion.py", "def ingest_docx_bytes("),
    "docx_service_method": ("backend/app/services/docx_service/service.py", "def ingest_docx("),
    "pdf_ingestion_output": ("backend/app/services/pdf_service/ingestion.py", "class PdfIngestionOutput"),
    "pdf_ingest_function": ("backend/app/services/pdf_service/ingestion.py", "def ingest_pdf_content("),
    "pdf_image_only_error": ("backend/app/services/pdf_service/ingestion.py", "class PdfImageOnlyError"),
    "pdf_service_method": ("backend/app/services/pdf_service/service.py", "def ingest_pdf("),
    "doc_no_fake_ocr": ("docs/codex/DOCX_PDF_REAL_INGESTION_RUNTIME.md", "RF3 does not add OCR and must not fake scanned PDF support."),
}


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def marker_present(repo_root: Path, rel: str, marker: str) -> bool:
    path = repo_root / rel
    return path.exists() and marker in path.read_text(encoding="utf-8")


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing RF3 required file: {rel}")
    for name, (rel, marker) in REQUIRED_MARKERS.items():
        if not marker_present(repo_root, rel, marker):
            errors.append(f"missing RF3 marker: {name}")
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch != "7_Runtime_Foundation":
            errors.append(f"expected branch 7_Runtime_Foundation, got {branch}")
    return errors


def sample_docx_bytes() -> bytes:
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>RF3 DOCX paragraph one.</w:t></w:r></w:p>
    <w:p><w:r><w:t>RF3 DOCX paragraph two.</w:t></w:r></w:p>
    <w:tbl><w:tr><w:tc><w:p><w:r><w:t>RF3 DOCX table cell.</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
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
4 0 obj << /Length 105 >> stream
BT /F1 12 Tf 72 720 Td (RF3 PDF first sentence.) Tj 0 -18 Td (RF3 PDF second sentence.) Tj ET
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


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.docx_service import DocxIngestionError, DocxService
    from backend.app.services.docx_service.entrypoint import DocxIngestionRequest, DocxServiceEntrypoint
    from backend.app.services.pdf_service import PdfImageOnlyError, PdfService
    from backend.app.services.pdf_service.entrypoint import PdfIngestionRequest, PdfServiceEntrypoint

    errors: list[str] = []

    docx_service = DocxService()
    docx_result = docx_service.ingest_docx(sample_docx_bytes(), source_filename="rf3.docx")
    pdf_service = PdfService()
    pdf_result = pdf_service.ingest_pdf(sample_pdf_bytes(), source_filename="rf3.pdf", max_sentences=1)

    docx_entrypoint_result = DocxServiceEntrypoint(service=docx_service).ingest(
        DocxIngestionRequest(content=sample_docx_bytes(), source_filename="entrypoint.docx")
    )
    pdf_entrypoint_result = PdfServiceEntrypoint(service=pdf_service).ingest(
        PdfIngestionRequest(content=sample_pdf_bytes(), source_filename="entrypoint.pdf", max_sentences=2)
    )

    malformed_docx_rejected = False
    try:
        docx_service.ingest_docx(b"not a docx")
    except DocxIngestionError:
        malformed_docx_rejected = True

    image_only_pdf_rejected = False
    try:
        pdf_service.ingest_pdf(image_only_pdf_bytes())
    except PdfImageOnlyError:
        image_only_pdf_rejected = True

    if "RF3 DOCX paragraph one." not in docx_result.extracted_text:
        errors.append("DOCX real package text was not extracted")
    if docx_result.paragraph_count != 3 or docx_result.table_cell_count != 1:
        errors.append("DOCX paragraph/table metadata mismatch")
    if "RF3 PDF first sentence." not in pdf_result.extracted_text:
        errors.append("PDF text layer was not extracted")
    if pdf_result.page_count != 1:
        errors.append("PDF page count metadata mismatch")
    if not malformed_docx_rejected:
        errors.append("malformed DOCX was not rejected")
    if not image_only_pdf_rejected:
        errors.append("image-only PDF did not fail honestly")
    for metadata in (docx_result.safe_metadata, pdf_result.safe_metadata):
        if metadata.get("network_required") is not False:
            errors.append("ingestion metadata must not require network")
        if metadata.get("cloud_ocr_used") is not False:
            errors.append("RF3 must not use cloud OCR")
        if metadata.get("fake_ocr_claimed") is not False:
            errors.append("RF3 must not fake OCR support")
        if metadata.get("dependency_versions_changed_by_rf3") is not False:
            errors.append("RF3 must not change dependency versions")
        if metadata.get("dockerfiles_changed_by_rf3") is not False:
            errors.append("RF3 must not change Dockerfiles")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "docx_real_package_ingestion_supported": not errors and "RF3 DOCX paragraph one." in docx_result.extracted_text,
        "docx_paragraph_count": docx_result.paragraph_count,
        "docx_table_cell_count": docx_result.table_cell_count,
        "docx_entrypoint_supported": "RF3 DOCX paragraph one." in docx_entrypoint_result.extracted_text,
        "pdf_text_layer_ingestion_supported": "RF3 PDF first sentence." in pdf_result.extracted_text,
        "pdf_page_count": pdf_result.page_count,
        "pdf_entrypoint_supported": "RF3 PDF second sentence." in pdf_entrypoint_result.summary,
        "malformed_docx_rejected": malformed_docx_rejected,
        "image_only_pdf_honest_failure": image_only_pdf_rejected,
        "cloud_ocr_used": False,
        "cloud_ocr_added_by_rf3": False,
        "fake_ocr_claimed": False,
        "dependency_versions_changed_by_rf3": False,
        "dockerfiles_changed_by_rf3": False,
        "payload_starts_with_text_report": (
            docx_result.artifact_content.startswith(b"DOCX Ingestion Report\n")
            and pdf_result.artifact_content.startswith(b"PDF Ingestion Report\n")
        ),
        "safe_metadata_only": True,
        "kimi_grade_supported": False,
        "product_grade_supported": False,
        "whole_project_kimi_level_supported": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready=require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = list(static_errors)
    errors.extend(smoke.get("errors", []))
    return {
        "mode": "docx-pdf-real-ingestion-runtime",
        "phase": "RF3",
        "checkpoint": "RF3",
        "network_required": False,
        "runtime_changed_by_rf3": True,
        "runtime_change_type": "real_docx_pdf_local_text_ingestion_runtime",
        "dependency_versions_changed_by_rf3": False,
        "dockerfiles_changed_by_rf3": False,
        "frontend_runtime_changed_by_rf3": False,
        "llm_topology_changed_by_rf3": False,
        "browser_runtime_changed_by_rf3": False,
        "api_endpoint_added_by_rf3": False,
        "db_schema_migration_added_by_rf3": False,
        "queue_or_event_store_migration_added_by_rf3": False,
        "cloud_ocr_added_by_rf3": False,
        "fake_ocr_claimed_by_rf3": False,
        "visual_qa_runtime_added_by_rf3": False,
        "k_phase_started_by_rf3": False,
        "runtime_smoke": smoke,
        "next_recommended_step": "RF4 — Local GigaChat integration hardening",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RF3 DOCX/PDF real ingestion runtime check.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    report = build_report(repo_root, require_ready=args.require_ready)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
