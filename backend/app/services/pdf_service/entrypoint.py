from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.pdf_service.service import PdfService


@dataclass(frozen=True)
class PdfSummaryRequest:
    content: str
    max_sentences: int = 2


@dataclass(frozen=True)
class PdfSummaryResult:
    summary: str


@dataclass
class PdfServiceEntrypoint:
    service: PdfService

    def summarize(self, request: PdfSummaryRequest) -> PdfSummaryResult:
        summary = self.service.summarize(request.content, max_sentences=request.max_sentences)
        return PdfSummaryResult(summary=summary)
