from backend.app.services.slides_service.approved_plan import (
    ApprovedPlanRenderRequest,
    ApprovedPlanRenderResult,
    render_approved_plan_to_pptx,
)
from backend.app.services.slides_service.approved_plan_lifecycle import (
    ApprovedPlanLifecycleRequest,
    ApprovedPlanLifecycleResult,
    SlidesTaskEvent,
    render_approved_plan_with_lifecycle,
)
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
from backend.app.services.slides_service.saved_plan_retry import (
    SavedPlanRetryRequest,
    SavedPlanRetryResult,
    retry_saved_plan_with_lifecycle,
)
from backend.app.services.slides_service.provenance_manifest_runtime import (
    PROVENANCE_MANIFEST_CONTENT_TYPE,
    SlidesGenerationProvenanceRuntimeResult,
    SlidesProvenanceManifestEmissionResult,
    SlidesRetryProvenanceRuntimeResult,
    build_generation_provenance_manifest,
    build_retry_provenance_manifest,
    emit_generation_provenance_manifest,
    emit_retry_provenance_manifest,
    verify_manifest_digest,
)
from backend.app.services.slides_service.render_mode_runtime import (
    RenderModeRuntimeRequest,
    RenderModeRuntimeResult,
    resolve_render_mode_runtime,
    slides_render_mode_runtime_capabilities,
)
from backend.app.services.slides_service.runtime_closure import (
    RF2_SLIDES_RUNTIME_NEXT_ROUTE,
    SlidesRuntimeClosureReadiness,
    build_slides_runtime_closure_readiness,
    validate_slides_runtime_closure_readiness,
)
from backend.app.services.slides_service.service import SlidesService, SlidesTransformOutput

__all__ = [
    "validate_slides_runtime_closure_readiness",
    "build_slides_runtime_closure_readiness",
    "SlidesRuntimeClosureReadiness",
    "RF2_SLIDES_RUNTIME_NEXT_ROUTE",
    "verify_manifest_digest",
    "emit_retry_provenance_manifest",
    "emit_generation_provenance_manifest",
    "build_retry_provenance_manifest",
    "build_generation_provenance_manifest",
    "SlidesRetryProvenanceRuntimeResult",
    "SlidesProvenanceManifestEmissionResult",
    "SlidesGenerationProvenanceRuntimeResult",
    "PROVENANCE_MANIFEST_CONTENT_TYPE",
    "slides_render_mode_runtime_capabilities",
    "resolve_render_mode_runtime",
    "RenderModeRuntimeResult",
    "RenderModeRuntimeRequest",
    "retry_saved_plan_with_lifecycle",
    "SavedPlanRetryResult",
    "SavedPlanRetryRequest",
    "render_approved_plan_with_lifecycle",
    "SlidesTaskEvent",
    "ApprovedPlanLifecycleResult",
    "ApprovedPlanLifecycleRequest",
    "render_approved_plan_to_pptx",
    "ApprovedPlanRenderResult",
    "ApprovedPlanRenderRequest",
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
