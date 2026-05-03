from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

PDF_INGESTION_ARTIFACT_CONTENT_TYPE = "text/plain; charset=utf-8"
PDF_MIME_TYPE = "application/pdf"

_TEXT_SHOW_RE = re.compile(rb"\((?:\\.|[^\\()])*\)\s*Tj")
_TEXT_ARRAY_RE = re.compile(rb"\[(.*?)\]\s*TJ", re.DOTALL)
_PAREN_STRING_RE = re.compile(rb"\((?:\\.|[^\\()])*\)")
_HEX_STRING_RE = re.compile(rb"<([0-9A-Fa-f\s]+)>")


class PdfIngestionError(ValueError):
    """Raised when PDF ingestion cannot safely extract a text layer."""


class PdfImageOnlyError(PdfIngestionError):
    """Raised for scanned/image-only PDFs when OCR is not available."""


@dataclass(frozen=True)
class PdfIngestionOutput:
    extracted_text: str
    summary: str
    page_count: int | None
    artifact_content: bytes
    content_type: str
    safe_metadata: dict[str, object]


def ingest_pdf_content(
    content: str | bytes,
    *,
    source_filename: str = "document.pdf",
    max_sentences: int = 2,
) -> PdfIngestionOutput:
    """Extract text from a PDF text layer or legacy plain text content.

    RF3 adds an honest local text-layer path. It does not add OCR and must fail
    explicitly for scanned/image-only PDFs instead of returning fabricated text.
    """

    raw = content.encode("utf-8") if isinstance(content, str) else bytes(content)
    if not raw:
        raise PdfIngestionError("PDF ingestion requires non-empty content.")

    is_pdf = raw.lstrip().startswith(b"%PDF")
    if is_pdf:
        extracted_text = _extract_text_from_pdf_bytes(raw)
        page_count = _count_pdf_pages(raw)
        source_kind = "pdf_text_layer"
    else:
        extracted_text = _normalize_text(raw.decode("utf-8", errors="ignore"))
        page_count = None
        source_kind = "legacy_plain_text_input"

    if not extracted_text:
        if is_pdf and _looks_image_only(raw):
            raise PdfImageOnlyError(
                "PDF appears to be scanned/image-only and has no extractable text layer; "
                "OCR is not implemented in RF3."
            )
        raise PdfIngestionError("PDF has no extractable text layer.")

    summary = _summarize_sentences(extracted_text, max_sentences=max_sentences)
    metadata = {
        "workflow_id": "documents.docx_pdf_ingestion_runtime",
        "schema_version": "docx_pdf_ingestion_rf3.v1",
        "source_format": "pdf",
        "source_kind": source_kind,
        "source_filename": _safe_filename(source_filename, default="document.pdf"),
        "mime_type": PDF_MIME_TYPE if is_pdf else "text/plain",
        "page_count": page_count,
        "extracted_text_chars": len(extracted_text),
        "summary_sentence_limit": max(max_sentences, 1),
        "artifact_content_type": PDF_INGESTION_ARTIFACT_CONTENT_TYPE,
        "network_required": False,
        "cloud_ocr_used": False,
        "ocr_runtime_added_by_rf3": False,
        "image_only_pdf_supported": False,
        "fake_ocr_claimed": False,
        "runtime_changed_by_rf3": True,
        "dependency_versions_changed_by_rf3": False,
        "dockerfiles_changed_by_rf3": False,
        "kimi_grade_supported": False,
        "whole_project_kimi_level_supported": False,
    }
    return PdfIngestionOutput(
        extracted_text=extracted_text,
        summary=summary,
        page_count=page_count,
        artifact_content=_render_pdf_ingestion_report(
            extracted_text=extracted_text,
            summary=summary,
            metadata=metadata,
        ),
        content_type=PDF_INGESTION_ARTIFACT_CONTENT_TYPE,
        safe_metadata=metadata,
    )


def _extract_text_from_pdf_bytes(raw: bytes) -> str:
    if b"/Encrypt" in raw:
        raise PdfIngestionError("Encrypted PDFs are not supported by the RF3 local text-layer extractor.")

    fragments: list[str] = []
    for match in _TEXT_SHOW_RE.finditer(raw):
        token = _PAREN_STRING_RE.search(match.group(0))
        if token:
            fragments.append(_decode_pdf_literal_string(token.group(0)))

    for array in _TEXT_ARRAY_RE.finditer(raw):
        body = array.group(1)
        parts = [_decode_pdf_literal_string(item.group(0)) for item in _PAREN_STRING_RE.finditer(body)]
        parts.extend(_decode_pdf_hex_string(item.group(1)) for item in _HEX_STRING_RE.finditer(body))
        if parts:
            fragments.append("".join(parts))

    return _normalize_text(" ".join(fragment for fragment in fragments if fragment))


def _decode_pdf_literal_string(token: bytes) -> str:
    assert token.startswith(b"(") and token.endswith(b")")
    body = token[1:-1]
    out = bytearray()
    i = 0
    while i < len(body):
        char = body[i]
        if char == 0x5C and i + 1 < len(body):  # backslash
            nxt = body[i + 1]
            escapes = {ord("n"): b"\n", ord("r"): b"\r", ord("t"): b"\t", ord("b"): b"\b", ord("f"): b"\f"}
            if nxt in escapes:
                out.extend(escapes[nxt])
            elif nxt in (ord("("), ord(")"), ord("\\")):
                out.append(nxt)
            else:
                out.append(nxt)
            i += 2
            continue
        out.append(char)
        i += 1
    return out.decode("utf-8", errors="ignore")


def _decode_pdf_hex_string(token: bytes) -> str:
    compact = re.sub(rb"\s+", b"", token)
    if len(compact) % 2:
        compact += b"0"
    try:
        return bytes.fromhex(compact.decode("ascii")).decode("utf-8", errors="ignore")
    except ValueError:
        return ""


def _count_pdf_pages(raw: bytes) -> int | None:
    count = len(re.findall(rb"/Type\s*/Page\b", raw))
    return count or None


def _looks_image_only(raw: bytes) -> bool:
    return b"/Subtype /Image" in raw or b"/Subtype/Image" in raw or b"/Image" in raw


def _summarize_sentences(text: str, *, max_sentences: int) -> str:
    segments = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]
    if not segments:
        return ""
    selected = segments[: max(max_sentences, 1)]
    return " ".join(selected)


def _render_pdf_ingestion_report(*, extracted_text: str, summary: str, metadata: dict[str, object]) -> bytes:
    report = (
        "PDF Ingestion Report\n"
        "====================\n\n"
        "Format: text/plain\n"
        "Source format: PDF\n"
        "Extractor: local text-layer parser\n"
        "Cloud OCR used: false\n"
        "Image-only PDF supported: false\n\n"
        "Metadata\n"
        "--------\n"
        f"source_kind: {metadata['source_kind']}\n"
        f"page_count: {metadata['page_count']}\n"
        f"extracted_text_chars: {metadata['extracted_text_chars']}\n\n"
        "Summary\n"
        "-------\n"
        f"{summary}\n\n"
        "Extracted Text\n"
        "--------------\n"
        f"{extracted_text}\n"
    )
    return report.encode("utf-8")


def _normalize_text(value: str) -> str:
    return " ".join(value.replace("\r", " ").replace("\n", " ").split())


def _safe_filename(value: str, *, default: str) -> str:
    name = (value or "").strip() or default
    if "/" in name or "\\" in name or ".." in name:
        return default
    return name
