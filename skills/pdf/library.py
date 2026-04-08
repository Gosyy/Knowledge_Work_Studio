from __future__ import annotations


def summarize_pdf_text(text: str, max_sentences: int = 2) -> str:
    """Deterministic sentence truncation helper representing migrated PDF logic."""
    segments = [segment.strip() for segment in text.replace("\n", " ").split(".") if segment.strip()]
    if not segments:
        return ""
    selected = segments[: max(max_sentences, 1)]
    return ". ".join(selected) + "."
