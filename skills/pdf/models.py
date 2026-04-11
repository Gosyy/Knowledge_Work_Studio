from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PdfExtractionResult:
    extracted_text: str


@dataclass(frozen=True)
class PdfSummaryPlan:
    max_sentences: int = 2
