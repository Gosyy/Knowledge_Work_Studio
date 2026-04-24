from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.slides_service.outline import SlideOutlineItem
from backend.app.services.slides_service.service import SlidesService


@dataclass(frozen=True)
class SlidesGenerateRequest:
    content: str
    template_id: str = "default_light"
    session_id: str | None = None
    task_id: str | None = None
    owner_user_id: str = "user_local_default"


@dataclass(frozen=True)
class SlidesGenerateResult:
    slide_count: int
    summary: str
    artifact_content: bytes
    outline: tuple[SlideOutlineItem, ...]
    generated_media_file_ids: tuple[str, ...] = ()


@dataclass
class SlidesServiceEntrypoint:
    service: SlidesService

    def generate(self, request: SlidesGenerateRequest) -> SlidesGenerateResult:
        output = self.service.generate_deck(
            request.content,
            template_id=request.template_id,
            session_id=request.session_id,
            task_id=request.task_id,
            owner_user_id=request.owner_user_id,
        )
        return SlidesGenerateResult(
            slide_count=output.slide_count,
            summary=output.summary_text,
            artifact_content=output.artifact_content,
            outline=output.outline,
            generated_media_file_ids=output.generated_media_file_ids,
        )
