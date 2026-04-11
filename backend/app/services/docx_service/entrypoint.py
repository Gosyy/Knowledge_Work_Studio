from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.docx_service.service import DocxService


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

    def transform(self, request: DocxTransformRequest) -> DocxTransformResult:
        updated = self.service.transform_document(
            request.content,
            target=request.target,
            replacement=request.replacement,
        )
        return DocxTransformResult(content=updated.content, artifact_content=updated.artifact_content)
