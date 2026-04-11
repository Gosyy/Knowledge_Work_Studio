from __future__ import annotations

from dataclasses import dataclass

from skills.pdf import extract_pdf_text, render_pdf_summary_report, summarize_pdf_text


@dataclass(frozen=True)
class PdfTransformOutput:
    extracted_text: str
    summary: str
    artifact_content: bytes


@dataclass
class PdfService:
    """Service-layer wrapper around reusable PDF skill logic."""

    def summarize(self, text: str, *, max_sentences: int = 2) -> str:
        return summarize_pdf_text(text, max_sentences=max_sentences)

    def transform_pdf(self, content: str | bytes, *, max_sentences: int = 2) -> PdfTransformOutput:
        extraction = extract_pdf_text(content)
        summary = summarize_pdf_text(extraction.extracted_text, max_sentences=max_sentences)
        artifact_content = render_pdf_summary_report(extraction.extracted_text, summary)
        return PdfTransformOutput(
            extracted_text=extraction.extracted_text,
            summary=summary,
            artifact_content=artifact_content,
        )
