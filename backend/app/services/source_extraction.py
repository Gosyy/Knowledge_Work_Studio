from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException, status

_TEXT_FILE_TYPES = {"txt", "md", "csv", "json", "yaml", "yml", "log"}
_DOCX_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_PPTX_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
_PDF_MIME_TYPES = {"application/pdf"}

_WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
_DRAWING_NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    outline_json: dict[str, object] | None = None
    content_kind: str = "extracted_text"


@dataclass(frozen=True)
class SlideOutlineEntry:
    title: str
    bullets: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"title": self.title, "bullets": list(self.bullets)}


class BinarySourceExtractor:
    def extract(
        self,
        *,
        raw_content: bytes,
        file_type: str,
        mime_type: str,
        source_label: str,
    ) -> ExtractionResult:
        normalized_file_type = (file_type or "").strip().lower()
        normalized_mime_type = (mime_type or "").strip().lower()

        if self._is_text_like(normalized_file_type, normalized_mime_type):
            return ExtractionResult(text=_decode_utf8_text(raw_content, source_label=source_label))
        if self._is_docx(normalized_file_type, normalized_mime_type):
            return ExtractionResult(text=_extract_docx_text(raw_content, source_label=source_label))
        if self._is_pptx(normalized_file_type, normalized_mime_type):
            slides = _extract_pptx_outline(raw_content, source_label=source_label)
            text = "\n\n".join(_render_slide_text(slide) for slide in slides)
            return ExtractionResult(
                text=text,
                outline_json={"slides": [slide.as_dict() for slide in slides]},
            )
        if self._is_pdf(normalized_file_type, normalized_mime_type):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"{source_label} is a PDF, but honest PDF text extraction is not wired in this deployment yet. "
                    "M8 does not fake PDF extraction or use OCR."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"{source_label} uses unsupported binary format '{file_type or mime_type or 'unknown'}'. "
                "Supported binary extraction in M8 is limited to DOCX and PPTX."
            ),
        )

    @staticmethod
    def _is_text_like(file_type: str, mime_type: str) -> bool:
        return mime_type.startswith("text/") or file_type in _TEXT_FILE_TYPES

    @staticmethod
    def _is_docx(file_type: str, mime_type: str) -> bool:
        return file_type == "docx" or mime_type in _DOCX_MIME_TYPES

    @staticmethod
    def _is_pptx(file_type: str, mime_type: str) -> bool:
        return file_type == "pptx" or mime_type in _PPTX_MIME_TYPES

    @staticmethod
    def _is_pdf(file_type: str, mime_type: str) -> bool:
        return file_type == "pdf" or mime_type in _PDF_MIME_TYPES


def _decode_utf8_text(raw_content: bytes, *, source_label: str) -> str:
    try:
        return raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"{source_label} is marked as text-compatible, but it is not valid UTF-8 text. "
                "M8 does not silently decode binary garbage as text."
            ),
        ) from exc


def _extract_docx_text(raw_content: bytes, *, source_label: str) -> str:
    try:
        with ZipFile(BytesIO(raw_content)) as package:
            document_xml = package.read("word/document.xml")
    except (BadZipFile, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{source_label} is not a valid DOCX package.",
        ) from exc

    root = ET.fromstring(document_xml)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", _WORD_NS):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", _WORD_NS)]
        if texts:
            paragraphs.append("".join(texts))
    if not paragraphs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{source_label} does not contain extractable DOCX text.",
        )
    return "\n".join(paragraphs)


def _extract_pptx_outline(raw_content: bytes, *, source_label: str) -> tuple[SlideOutlineEntry, ...]:
    try:
        with ZipFile(BytesIO(raw_content)) as package:
            slide_names = sorted(
                (name for name in package.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")),
                key=_slide_sort_key,
            )
            slide_xml_blobs = [package.read(name) for name in slide_names]
    except BadZipFile as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{source_label} is not a valid PPTX package.",
        ) from exc

    if not slide_xml_blobs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{source_label} does not contain extractable PPTX slides.",
        )

    slides: list[SlideOutlineEntry] = []
    for index, xml_blob in enumerate(slide_xml_blobs, start=1):
        root = ET.fromstring(xml_blob)
        texts = [node.text or "" for node in root.findall(".//a:t", _DRAWING_NS) if (node.text or "").strip()]
        if not texts:
            continue
        title = texts[0]
        bullets = tuple(texts[1:]) or (title,)
        slides.append(SlideOutlineEntry(title=title, bullets=bullets))

    if not slides:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{source_label} does not contain extractable PPTX text.",
        )
    return tuple(slides)


def _slide_sort_key(name: str) -> tuple[int, str]:
    stem = name.rsplit("/", 1)[-1].removesuffix(".xml")
    suffix = stem.replace("slide", "")
    return (int(suffix) if suffix.isdigit() else 10**9, name)


def _render_slide_text(slide: SlideOutlineEntry) -> str:
    unique_bullets = [bullet for bullet in slide.bullets if bullet != slide.title]
    if not unique_bullets:
        return slide.title
    return "\n".join([slide.title, *unique_bullets])


__all__ = ["BinarySourceExtractor", "ExtractionResult"]
