from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.pdf_service.service import PdfService


@dataclass(frozen=True)
class PdfSummaryRequest:
    content: str
    max_sentences: int = 2


@dataclass(frozen=True)
class PdfSummaryResult:
    extracted_text: str
    summary: str
    artifact_content: bytes


@dataclass
class PdfServiceEntrypoint:
    service: PdfService

    def summarize(self, request: PdfSummaryRequest) -> PdfSummaryResult:
        transformed = self.service.transform_pdf(request.content, max_sentences=request.max_sentences)
        return PdfSummaryResult(
            extracted_text=transformed.extracted_text,
            summary=transformed.summary,
            artifact_content=transformed.artifact_content,
        )
