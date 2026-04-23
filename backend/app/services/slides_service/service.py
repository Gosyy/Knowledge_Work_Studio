from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.slides_service.generator import generate_pptx_from_plan
from backend.app.services.slides_service.outline import PresentationPlan, SlideOutlineItem, build_presentation_plan, plan_to_outline


@dataclass(frozen=True)
class SlidesTransformOutput:
    slide_count: int
    summary_text: str
    artifact_content: bytes
    outline: tuple[SlideOutlineItem, ...]
    plan: PresentationPlan
    template_id: str


@dataclass
class SlidesService:
    """Planning-first deterministic, layout-aware slides MVP generator."""

    def generate_deck(self, source_text: str, *, template_id: str = "default_light") -> SlidesTransformOutput:
        plan = build_presentation_plan(source_text, min_slides=5, max_slides=10)
        outline = plan_to_outline(plan)
        slide_count = len(outline)
        artifact_content = generate_pptx_from_plan(plan, template_id=template_id)
        summary_text = f"Generated {slide_count} slide(s)." if template_id == "default_light" else f"Generated {slide_count} slide(s) with template '{template_id}'."
        return SlidesTransformOutput(
            slide_count=slide_count,
            summary_text=summary_text,
            artifact_content=artifact_content,
            outline=outline,
            plan=plan,
            template_id=template_id,
        )
