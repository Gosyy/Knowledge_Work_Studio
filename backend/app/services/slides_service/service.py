from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.slides_service.generator import generate_pptx_from_outline
from backend.app.services.slides_service.outline import SlideOutlineItem, build_slides_outline


@dataclass(frozen=True)
class SlidesTransformOutput:
    slide_count: int
    summary_text: str
    artifact_content: bytes
    outline: tuple[SlideOutlineItem, ...]


@dataclass
class SlidesService:
    """Outline-first deterministic, source-aware slides MVP generator."""

    def generate_deck(self, source_text: str) -> SlidesTransformOutput:
        outline = build_slides_outline(source_text, min_slides=5, max_slides=10)
        slide_count = len(outline)
        artifact_content = generate_pptx_from_outline(outline)
        summary_text = f"Generated {slide_count} slide(s)."
        return SlidesTransformOutput(
            slide_count=slide_count,
            summary_text=summary_text,
            artifact_content=artifact_content,
            outline=outline,
        )
