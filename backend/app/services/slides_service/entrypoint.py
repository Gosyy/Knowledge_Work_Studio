from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.slides_service.service import SlidesService


@dataclass(frozen=True)
class SlidesGenerateRequest:
    content: str


@dataclass(frozen=True)
class SlidesGenerateResult:
    slide_count: int
    summary: str
    artifact_content: bytes


@dataclass
class SlidesServiceEntrypoint:
    service: SlidesService

    def generate(self, request: SlidesGenerateRequest) -> SlidesGenerateResult:
        output = self.service.generate_deck(request.content)
        return SlidesGenerateResult(
            slide_count=output.slide_count,
            summary=output.summary_text,
            artifact_content=output.artifact_content,
        )
