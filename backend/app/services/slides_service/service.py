from __future__ import annotations

from dataclasses import dataclass, field, replace

from backend.app.services.slides_service.generator import generate_pptx_from_plan
from backend.app.services.slides_service.image_pipeline import DeterministicPatternImageProvider, SlideImageProvider, SlideImageRegistry
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideOutlineItem, build_presentation_plan, plan_to_outline


@dataclass(frozen=True)
class SlidesTransformOutput:
    slide_count: int
    summary_text: str
    artifact_content: bytes
    outline: tuple[SlideOutlineItem, ...]
    plan: PresentationPlan
    template_id: str
    generated_media_file_ids: tuple[str, ...] = ()


@dataclass
class SlidesService:
    """Planning-first, layout-aware, image-capable slides MVP generator."""

    image_provider: SlideImageProvider = field(default_factory=DeterministicPatternImageProvider)
    image_registry: SlideImageRegistry | None = None

    def generate_deck(
        self,
        source_text: str,
        *,
        template_id: str = "default_light",
        session_id: str | None = None,
        task_id: str | None = None,
        owner_user_id: str = "user_local_default",
    ) -> SlidesTransformOutput:
        plan = build_presentation_plan(source_text, min_slides=5, max_slides=10)
        enriched_plan, stored_file_ids = self._attach_generated_visuals(
            plan,
            session_id=session_id,
            task_id=task_id,
            owner_user_id=owner_user_id,
        )
        outline = plan_to_outline(enriched_plan)
        slide_count = len(outline)
        artifact_content = generate_pptx_from_plan(enriched_plan, template_id=template_id)
        summary_text = (
            f"Generated {slide_count} slide(s)."
            if template_id == "default_light"
            else f"Generated {slide_count} slide(s) with template '{template_id}'."
        )
        return SlidesTransformOutput(
            slide_count=slide_count,
            summary_text=summary_text,
            artifact_content=artifact_content,
            outline=outline,
            plan=enriched_plan,
            template_id=template_id,
            generated_media_file_ids=stored_file_ids,
        )

    def _attach_generated_visuals(
        self,
        plan: PresentationPlan,
        *,
        session_id: str | None,
        task_id: str | None,
        owner_user_id: str,
    ) -> tuple[PresentationPlan, tuple[str, ...]]:
        updated_slides: list[PlannedSlide] = []
        stored_file_ids: list[str] = []
        for slide in plan.slides:
            if not slide.image_specs:
                updated_slides.append(slide)
                continue

            assets = []
            for spec in slide.image_specs:
                asset = self.image_provider.generate(spec)
                if self.image_registry is not None and session_id is not None and task_id is not None:
                    registered = self.image_registry.register_generated_asset(
                        session_id=session_id,
                        task_id=task_id,
                        owner_user_id=owner_user_id,
                        spec=spec,
                        asset=asset,
                    )
                    asset = registered.asset
                    stored_file_ids.append(registered.stored_file.id)
                assets.append(asset)
            updated_slides.append(replace(slide, media_assets=tuple(assets)))

        return replace(plan, slides=tuple(updated_slides)), tuple(stored_file_ids)
