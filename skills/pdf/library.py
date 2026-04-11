from __future__ import annotations

from skills.pdf.models import PdfExtractionResult, PdfSummaryPlan


def extract_pdf_text(content: str | bytes) -> PdfExtractionResult:
    """Deterministic extraction helper for plain-text-like PDF payloads."""
    raw_text = content.decode("utf-8", errors="ignore") if isinstance(content, bytes) else content
    normalized = " ".join(raw_text.replace("\r", " ").replace("\n", " ").split())
    return PdfExtractionResult(extracted_text=normalized)


def summarize_pdf_text(text: str, max_sentences: int = 2) -> str:
    plan = PdfSummaryPlan(max_sentences=max_sentences)
    segments = [segment.strip() for segment in text.replace("\n", " ").split(".") if segment.strip()]
    if not segments:
        return ""
    selected = segments[: max(plan.max_sentences, 1)]
    return ". ".join(selected) + "."


def render_pdf_summary_report(extracted_text: str, summary: str) -> bytes:
    report = f"PDF Summary Report\n\nSummary:\n{summary}\n\nExtracted Text:\n{extracted_text}\n"
    return report.encode("utf-8")
