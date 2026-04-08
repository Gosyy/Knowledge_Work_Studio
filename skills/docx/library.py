from __future__ import annotations

from skills.docx.models import DocxEditPlan


def apply_docx_edit_plan(document_text: str, plan: DocxEditPlan) -> str:
    """Deterministic text-level adapter representing migrated DOCX edit logic.

    This is intentionally simple and testable while service integrations are incremental.
    """
    if plan.operation == "replace":
        return document_text.replace(plan.target, plan.replacement)
    raise ValueError(f"Unsupported DOCX operation: {plan.operation}")
