from __future__ import annotations

from dataclasses import dataclass

from skills.docx import DocxEditPlan, apply_docx_edit_plan


@dataclass
class DocxService:
    """Service-layer wrapper around reusable DOCX skill logic."""

    def apply_edit(self, document_text: str, *, target: str, replacement: str) -> str:
        plan = DocxEditPlan(operation="replace", target=target, replacement=replacement)
        return apply_docx_edit_plan(document_text, plan)
