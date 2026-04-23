from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.slides_service.generator import generate_pptx_from_outline
from backend.app.services.slides_service.outline import PresentationPlan, SlideOutlineItem, build_presentation_plan, plan_to_outline


@dataclass(frozen=True)
class SlidesTransformOutput:
    slide_count: int
    summary_text: str
    artifact_content: bytes
    outline: tuple[SlideOutlineItem, ...]
    plan: PresentationPlan


@dataclass
class SlidesService:
    """Planning-first deterministic, source-aware slides MVP generator."""

    def generate_deck(self, source_text: str) -> SlidesTransformOutput:
        plan = build_presentation_plan(source_text, min_slides=5, max_slides=10)
        outline = plan_to_outline(plan)
        slide_count = len(outline)
        artifact_content = generate_pptx_from_outline(outline)
        summary_text = f"Generated {slide_count} slide(s)."
        return SlidesTransformOutput(
            slide_count=slide_count,
            summary_text=summary_text,
            artifact_content=artifact_content,
            outline=outline,
            plan=plan,
        )
