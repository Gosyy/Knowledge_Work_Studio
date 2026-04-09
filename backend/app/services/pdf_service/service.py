from __future__ import annotations

from dataclasses import dataclass

from skills.pdf import summarize_pdf_text


@dataclass
class PdfService:
    """Service-layer wrapper around reusable PDF skill logic."""

    def summarize(self, text: str, *, max_sentences: int = 2) -> str:
        return summarize_pdf_text(text, max_sentences=max_sentences)
