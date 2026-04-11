from backend.app.services.slides_service.entrypoint import SlidesGenerateRequest, SlidesGenerateResult, SlidesServiceEntrypoint
from backend.app.services.slides_service.generator import generate_pptx_from_outline
from backend.app.services.slides_service.outline import SlideOutlineItem, build_slides_outline
from backend.app.services.slides_service.service import SlidesService, SlidesTransformOutput

__all__ = [
    "SlideOutlineItem",
    "SlidesGenerateRequest",
    "SlidesGenerateResult",
    "SlidesService",
    "SlidesServiceEntrypoint",
    "SlidesTransformOutput",
    "build_slides_outline",
    "generate_pptx_from_outline",
]
