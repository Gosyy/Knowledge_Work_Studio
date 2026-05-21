from __future__ import annotations

from dataclasses import dataclass

from skills.pdf import summarize_pdf_text

from backend.app.services.pdf_service.ingestion import (
    PdfImageOnlyError,
    PdfIngestionError,
    PdfIngestionOutput,
    ingest_pdf_content,
)


@dataclass(frozen=True)
class PdfTransformOutput:
    extracted_text: str
    summary: str
    artifact_content: bytes


@dataclass
class PdfService:
    """Service-layer wrapper for honest text report output from PDF/source content.

    J2 deliberately produces a text report artifact, not a PDF binary. The
    orchestrator labels this output as summary.txt / text/plain, so artifact
    metadata matches the actual bytes.
    """

    def ingest_pdf(
        self,
        content: str | bytes,
        *,
        source_filename: str = "document.pdf",
        max_sentences: int = 2,
    ) -> PdfIngestionOutput:
        return ingest_pdf_content(
            content,
            source_filename=source_filename,
            max_sentences=max_sentences,
        )

    def summarize(self, text: str, *, max_sentences: int = 2) -> str:
        return summarize_pdf_text(text, max_sentences=max_sentences)

    def transform_pdf(self, content: str | bytes, *, max_sentences: int = 2) -> PdfTransformOutput:
        ingestion = self.ingest_pdf(content, max_sentences=max_sentences)
        artifact_content = self._render_text_summary_report(
            extracted_text=ingestion.extracted_text,
            summary=ingestion.summary,
        )
        return PdfTransformOutput(
            extracted_text=ingestion.extracted_text,
            summary=ingestion.summary,
            artifact_content=artifact_content,
        )

    @staticmethod
    def _render_text_summary_report(*, extracted_text: str, summary: str) -> bytes:
        report = (
            "Summary Report\n"
            "==============\n\n"
            "Format: text/plain\n"
            "This artifact is an honest text report, not a PDF binary.\n\n"
            "Summary\n"
            "-------\n"
            f"{summary}\n\n"
            "Extracted Text\n"
            "--------------\n"
            f"{extracted_text}\n"
        )
        return report.encode("utf-8")
