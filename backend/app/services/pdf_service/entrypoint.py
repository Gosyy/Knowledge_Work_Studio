from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.pdf_service.service import PdfService


@dataclass(frozen=True)
class PdfIngestionRequest:
    content: str | bytes
    source_filename: str = "document.pdf"
    max_sentences: int = 2


@dataclass(frozen=True)
class PdfIngestionResult:
    extracted_text: str
    summary: str
    page_count: int | None
    artifact_content: bytes
    content_type: str
    safe_metadata: dict[str, object]


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

    def ingest(self, request: PdfIngestionRequest) -> PdfIngestionResult:
        ingested = self.service.ingest_pdf(
            request.content,
            source_filename=request.source_filename,
            max_sentences=request.max_sentences,
        )
        return PdfIngestionResult(
            extracted_text=ingested.extracted_text,
            summary=ingested.summary,
            page_count=ingested.page_count,
            artifact_content=ingested.artifact_content,
            content_type=ingested.content_type,
            safe_metadata=ingested.safe_metadata,
        )

    def summarize(self, request: PdfSummaryRequest) -> PdfSummaryResult:
        transformed = self.service.transform_pdf(request.content, max_sentences=request.max_sentences)
        return PdfSummaryResult(
            extracted_text=transformed.extracted_text,
            summary=transformed.summary,
            artifact_content=transformed.artifact_content,
        )
