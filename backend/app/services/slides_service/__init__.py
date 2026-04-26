from backend.app.services.slides_service.entrypoint import SlidesGenerateRequest, SlidesGenerateResult, SlidesServiceEntrypoint
from backend.app.services.slides_service.generator import generate_pptx_from_outline, generate_pptx_from_plan
from backend.app.services.slides_service.image_pipeline import (
    DeterministicPatternImageProvider,
    ImageSpec,
    RegisteredSlideMedia,
    SlideImageProvider,
    SlideImageRegistry,
    VisualIntent,
)
from backend.app.services.slides_service.layouts import ImagePlaceholderBox, ResolvedSlideLayout, ShapeBox, SlideLayoutSpec, SlideTemplate, get_template, get_template_registry, resolve_layout_for_slide
from backend.app.services.slides_service.media import ImageFitMode, SlideMediaAsset
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideOutlineItem, SlideType, StoryArcStage, build_presentation_plan, build_slides_outline, plan_to_outline
from backend.app.services.slides_service.plan_snapshot import (
    PresentationPlanSnapshotService,
    deserialize_presentation_plan,
    serialize_presentation_plan,
)


from backend.app.services.slides_service.revision import (
    DeckRestoreRequest,
    DeckRestoreResult,
    DeckRevisionRequest,
    DeckRevisionResult,
    DeckRevisionScope,
    DeckRevisionService,
    SlideRevisionDelta,
)
from backend.app.services.slides_service.revision_strategy import (
    DeterministicRevisionStrategy,
    LLMRevisionStrategy,
    LLMRevisionPayload,
    SlideRevisionStrategy,
)
from backend.app.services.slides_service.source_grounding import (
    SlideCitation,
    SourceFragment,
    SourceGroundingResult,
    SourceReference,
    build_source_grounded_plan,
    render_slide_citations_xml,
)
from backend.app.services.slides_service.service import SlidesService, SlidesTransformOutput

__all__ = [
    "DeterministicPatternImageProvider",
    "SlideRevisionDelta",
    "SlideRevisionStrategy",
    "LLMRevisionPayload",
    "LLMRevisionStrategy",
    "DeterministicRevisionStrategy",
    "DeckRevisionService",
    "DeckRevisionScope",
    "DeckRestoreResult",
    "DeckRestoreRequest",
    "DeckRevisionResult",
    "DeckRevisionRequest",
    "ImageFitMode",
    "ImagePlaceholderBox",
    "ImageSpec",
    "PlannedSlide",
    "PresentationPlanSnapshotService",
    "deserialize_presentation_plan",
    "serialize_presentation_plan",
    "PresentationPlan",
    "RegisteredSlideMedia",
    "ResolvedSlideLayout",
    "ShapeBox",
    "SlideImageProvider",
    "SlideImageRegistry",
    "render_slide_citations_xml",
    "build_source_grounded_plan",
    "SourceReference",
    "SourceGroundingResult",
    "SourceFragment",
    "SlideCitation",
    "SlideLayoutSpec",
    "SlideMediaAsset",
    "SlideOutlineItem",
    "SlideTemplate",
    "SlideType",
    "SlidesGenerateRequest",
    "SlidesGenerateResult",
    "SlidesService",
    "SlidesServiceEntrypoint",
    "SlidesTransformOutput",
    "StoryArcStage",
    "VisualIntent",
    "build_presentation_plan",
    "build_slides_outline",
    "generate_pptx_from_outline",
    "generate_pptx_from_plan",
    "get_template",
    "get_template_registry",
    "plan_to_outline",
    "resolve_layout_for_slide",
]
