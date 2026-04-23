from fastapi import HTTPException
import pytest

from backend.app.services.docx_service.builder import build_docx_package
from backend.app.services.slides_service.generator import generate_pptx_from_outline
from backend.app.services.slides_service.outline import SlideOutlineItem
from backend.app.services.source_extraction import BinarySourceExtractor


def test_m8_extracts_docx_text_from_generated_package() -> None:
    extractor = BinarySourceExtractor()
    payload = build_docx_package("# Heading\nAlpha paragraph.\nBeta paragraph.")

    result = extractor.extract(
        raw_content=payload,
        file_type="docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        source_label="uploaded source 'upl_docx'",
    )

    assert result.content_kind == "extracted_text"
    assert result.outline_json is None
    assert result.text == "Heading\nAlpha paragraph.\nBeta paragraph."


def test_m8_extracts_pptx_text_and_outline_from_generated_package() -> None:
    extractor = BinarySourceExtractor()
    payload = generate_pptx_from_outline(
        (
            SlideOutlineItem(title="Roadmap", bullets=("Phase 1", "Phase 2")),
            SlideOutlineItem(title="Risks", bullets=("Budget", "Timeline")),
        )
    )

    result = extractor.extract(
        raw_content=payload,
        file_type="pptx",
        mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        source_label="presentation 'pres_1'",
    )

    assert result.content_kind == "extracted_text"
    assert result.outline_json == {
        "slides": [
            {"title": "Roadmap", "bullets": ["Phase 1", "Phase 2"]},
            {"title": "Risks", "bullets": ["Budget", "Timeline"]},
        ]
    }
    assert "Roadmap" in result.text
    assert "Phase 1" in result.text
    assert "Risks" in result.text


def test_m8_invalid_utf8_text_fails_honestly() -> None:
    extractor = BinarySourceExtractor()

    with pytest.raises(HTTPException) as exc_info:
        extractor.extract(
            raw_content=b"\xff\xfe\x00\x00",
            file_type="txt",
            mime_type="text/plain",
            source_label="uploaded source 'upl_bad'",
        )

    assert exc_info.value.status_code == 409
    assert "not valid UTF-8 text" in exc_info.value.detail


def test_m8_pdf_extraction_is_not_faked() -> None:
    extractor = BinarySourceExtractor()

    with pytest.raises(HTTPException) as exc_info:
        extractor.extract(
            raw_content=b"%PDF-1.4\n%fake\n",
            file_type="pdf",
            mime_type="application/pdf",
            source_label="stored file 'sf_pdf'",
        )

    assert exc_info.value.status_code == 409
    assert "does not fake PDF extraction" in exc_info.value.detail
