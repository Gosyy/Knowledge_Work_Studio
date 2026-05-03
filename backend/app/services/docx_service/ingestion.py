from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Any
from zipfile import BadZipFile, ZipFile, is_zipfile
from xml.etree import ElementTree as ET

DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
DOCX_INGESTION_ARTIFACT_CONTENT_TYPE = "text/plain; charset=utf-8"
_WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class DocxIngestionError(ValueError):
    """Raised when DOCX ingestion cannot safely extract text."""


@dataclass(frozen=True)
class DocxIngestionOutput:
    extracted_text: str
    paragraph_count: int
    table_cell_count: int
    artifact_content: bytes
    content_type: str
    safe_metadata: dict[str, object]


def ingest_docx_bytes(content: bytes, *, source_filename: str = "document.docx") -> DocxIngestionOutput:
    """Extract text from a real DOCX package using only stdlib parsers.

    RF3 intentionally avoids cloud parsers and dependency changes. It supports
    normal text-bearing DOCX files and fails honestly for malformed/non-DOCX
    inputs instead of pretending ingestion succeeded.
    """

    if not isinstance(content, bytes) or not content:
        raise DocxIngestionError("DOCX ingestion requires non-empty DOCX bytes.")
    if not is_zipfile(BytesIO(content)):
        raise DocxIngestionError("DOCX ingestion requires a valid DOCX/ZIP package.")

    try:
        with ZipFile(BytesIO(content), "r") as package:
            if "word/document.xml" not in package.namelist():
                raise DocxIngestionError("DOCX package is missing word/document.xml.")
            document_xml = package.read("word/document.xml")
    except BadZipFile as exc:
        raise DocxIngestionError("DOCX ingestion requires a readable DOCX/ZIP package.") from exc

    try:
        root = ET.fromstring(document_xml)
    except ET.ParseError as exc:
        raise DocxIngestionError("DOCX document.xml is not parseable XML.") from exc

    paragraphs: list[str] = []
    for paragraph in root.iter(f"{_WORD_NS}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{_WORD_NS}t"))
        text = _normalize_inline_text(text)
        if text:
            paragraphs.append(text)

    extracted_text = "\n".join(paragraphs).strip()
    if not extracted_text:
        raise DocxIngestionError("DOCX contains no extractable text paragraphs.")

    table_cell_count = sum(1 for _ in root.iter(f"{_WORD_NS}tc"))
    metadata = {
        "workflow_id": "documents.docx_pdf_ingestion_runtime",
        "schema_version": "docx_pdf_ingestion_rf3.v1",
        "source_format": "docx",
        "source_filename": _safe_filename(source_filename, default="document.docx"),
        "mime_type": DOCX_MIME_TYPE,
        "paragraph_count": len(paragraphs),
        "table_cell_count": table_cell_count,
        "extracted_text_chars": len(extracted_text),
        "artifact_content_type": DOCX_INGESTION_ARTIFACT_CONTENT_TYPE,
        "network_required": False,
        "cloud_ocr_used": False,
        "fake_ocr_claimed": False,
        "runtime_changed_by_rf3": True,
        "dependency_versions_changed_by_rf3": False,
        "dockerfiles_changed_by_rf3": False,
        "kimi_grade_supported": False,
        "whole_project_kimi_level_supported": False,
    }
    return DocxIngestionOutput(
        extracted_text=extracted_text,
        paragraph_count=len(paragraphs),
        table_cell_count=table_cell_count,
        artifact_content=_render_docx_ingestion_report(extracted_text=extracted_text, metadata=metadata),
        content_type=DOCX_INGESTION_ARTIFACT_CONTENT_TYPE,
        safe_metadata=metadata,
    )


def _render_docx_ingestion_report(*, extracted_text: str, metadata: dict[str, object]) -> bytes:
    report = (
        "DOCX Ingestion Report\n"
        "=====================\n\n"
        "Format: text/plain\n"
        "Source format: DOCX\n"
        "Extractor: stdlib zip+xml text layer\n"
        "Cloud OCR used: false\n\n"
        "Metadata\n"
        "--------\n"
        f"paragraph_count: {metadata['paragraph_count']}\n"
        f"table_cell_count: {metadata['table_cell_count']}\n"
        f"extracted_text_chars: {metadata['extracted_text_chars']}\n\n"
        "Extracted Text\n"
        "--------------\n"
        f"{extracted_text}\n"
    )
    return report.encode("utf-8")


def _normalize_inline_text(value: str) -> str:
    return re.sub(r"[ \t]+", " ", value).strip()


def _safe_filename(value: str, *, default: str) -> str:
    name = (value or "").strip() or default
    if "/" in name or "\\" in name or ".." in name:
        return default
    return name
