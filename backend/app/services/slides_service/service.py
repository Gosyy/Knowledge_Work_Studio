from __future__ import annotations

from dataclasses import dataclass
import io
import zipfile


@dataclass(frozen=True)
class SlidesTransformOutput:
    slide_count: int
    summary_text: str
    artifact_content: bytes


@dataclass
class SlidesService:
    """Minimal fixed-template slides MVP generator."""

    def generate_deck(self, source_text: str) -> SlidesTransformOutput:
        sections = [segment.strip() for segment in source_text.replace("\n", ". ").split(".") if segment.strip()]
        if not sections:
            sections = ["Untitled Slide"]

        slide_lines = sections[:5]
        slide_count = len(slide_lines)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as pptx_zip:
            pptx_zip.writestr("[Content_Types].xml", "<Types></Types>")
            for index, line in enumerate(slide_lines, start=1):
                pptx_zip.writestr(f"ppt/slides/slide{index}.txt", line)

        summary_text = f"Generated {slide_count} slide(s)."
        return SlidesTransformOutput(slide_count=slide_count, summary_text=summary_text, artifact_content=buffer.getvalue())
