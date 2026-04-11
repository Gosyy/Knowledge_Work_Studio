from __future__ import annotations

from skills.docx.models import DocxEditPlan, DocxRewritePlan


def apply_docx_edit_plan(document_text: str, plan: DocxEditPlan) -> str:
    """Deterministic text-level adapter representing migrated DOCX edit logic.

    This is intentionally simple and testable while service integrations are incremental.
    """
    if plan.operation == "replace":
        return document_text.replace(plan.target, plan.replacement)
    raise ValueError(f"Unsupported DOCX operation: {plan.operation}")


def apply_docx_rewrite_plan(document_text: str, plan: DocxRewritePlan) -> str:
    revised = document_text
    for source, target in plan.replacements:
        revised = revised.replace(source, target)

    if not plan.normalize_headings:
        return revised

    normalized_lines: list[str] = []
    for line in revised.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            heading = stripped[2:].strip().title()
            normalized_lines.append(f"# {heading}")
        elif stripped.endswith(":"):
            normalized_lines.append(stripped[:-1].strip().title() + ":")
        else:
            normalized_lines.append(line)

    return "\n".join(normalized_lines)
