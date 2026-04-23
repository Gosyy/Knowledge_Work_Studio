from backend.app.services.slides_service.entrypoint import SlidesGenerateRequest, SlidesGenerateResult, SlidesServiceEntrypoint
from backend.app.services.slides_service.generator import generate_pptx_from_outline, generate_pptx_from_plan
from backend.app.services.slides_service.layouts import ResolvedSlideLayout, ShapeBox, SlideLayoutSpec, SlideTemplate, get_template, get_template_registry, resolve_layout_for_slide
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideOutlineItem, SlideType, StoryArcStage, build_presentation_plan, build_slides_outline, plan_to_outline
from backend.app.services.slides_service.service import SlidesService, SlidesTransformOutput

__all__ = [
    "PlannedSlide",
    "PresentationPlan",
    "ResolvedSlideLayout",
    "ShapeBox",
    "SlideLayoutSpec",
    "SlideOutlineItem",
    "SlideTemplate",
    "SlideType",
    "SlidesGenerateRequest",
    "SlidesGenerateResult",
    "SlidesService",
    "SlidesServiceEntrypoint",
    "SlidesTransformOutput",
    "StoryArcStage",
    "build_presentation_plan",
    "build_slides_outline",
    "generate_pptx_from_outline",
    "generate_pptx_from_plan",
    "get_template",
    "get_template_registry",
    "plan_to_outline",
    "resolve_layout_for_slide",
]
