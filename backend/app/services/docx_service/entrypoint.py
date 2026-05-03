from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.docx_service.ingestion import DocxIngestionOutput
from backend.app.services.docx_service.service import DocxService


@dataclass(frozen=True)
class DocxIngestionRequest:
    content: bytes
    source_filename: str = "document.docx"


@dataclass(frozen=True)
class DocxIngestionResult:
    extracted_text: str
    paragraph_count: int
    table_cell_count: int
    artifact_content: bytes
    content_type: str
    safe_metadata: dict[str, object]


@dataclass(frozen=True)
class DocxTransformRequest:
    content: str
    target: str
    replacement: str


@dataclass(frozen=True)
class DocxTransformResult:
    content: str
    artifact_content: bytes


@dataclass
class DocxServiceEntrypoint:
    service: DocxService

    def ingest(self, request: DocxIngestionRequest) -> DocxIngestionResult:
        ingested = self.service.ingest_docx(
            request.content,
            source_filename=request.source_filename,
        )
        return DocxIngestionResult(
            extracted_text=ingested.extracted_text,
            paragraph_count=ingested.paragraph_count,
            table_cell_count=ingested.table_cell_count,
            artifact_content=ingested.artifact_content,
            content_type=ingested.content_type,
            safe_metadata=ingested.safe_metadata,
        )

    def transform(self, request: DocxTransformRequest) -> DocxTransformResult:
        updated = self.service.transform_document(
            request.content,
            target=request.target,
            replacement=request.replacement,
        )
        return DocxTransformResult(content=updated.content, artifact_content=updated.artifact_content)
