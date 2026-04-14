from __future__ import annotations

from dataclasses import dataclass

from skills.docx import DocxEditPlan, DocxRewritePlan, apply_docx_edit_plan, apply_docx_rewrite_plan

from backend.app.services.docx_service.builder import build_docx_package


@dataclass(frozen=True)
class DocxTransformOutput:
    content: str
    artifact_content: bytes


@dataclass
class DocxService:
    """Service-layer wrapper around reusable DOCX skill logic and deterministic DOCX packaging."""

    def apply_edit(self, document_text: str, *, target: str, replacement: str) -> str:
        plan = DocxEditPlan(operation="replace", target=target, replacement=replacement)
        return apply_docx_edit_plan(document_text, plan)

    def transform_document(self, document_text: str, *, target: str, replacement: str) -> DocxTransformOutput:
        plan = DocxRewritePlan(replacements=((target, replacement),), normalize_headings=True)
        revised_content = apply_docx_rewrite_plan(document_text, plan)
        artifact_payload = build_docx_package(revised_content)
        return DocxTransformOutput(content=revised_content, artifact_content=artifact_payload)
