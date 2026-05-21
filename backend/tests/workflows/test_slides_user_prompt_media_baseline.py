from __future__ import annotations

from io import BytesIO
import zipfile

from backend.app.services.slides_service.service import SlidesService


REAL_USER_PROMPT = (
    "Сгенерируй презентацию на 6 слайдов на тему: как компания может внедрить "
    "внутреннюю систему Knowledge Work Studio для работы с документами, таблицами, "
    "PDF, презентациями и проверяемыми артефактами. Стиль: деловой, понятно для "
    "руководителя, с краткими тезисами."
)

FORBIDDEN_PUBLIC_TEXT = (
    "Additional insight",
    "Local deterministic slide image generation",
    "Сгенерируй презентацию",
)


def _pptx_xml(payload: bytes) -> str:
    with zipfile.ZipFile(BytesIO(payload), "r") as pptx:
        return "\n".join(
            pptx.read(name).decode("utf-8", errors="replace")
            for name in pptx.namelist()
            if name.endswith(".xml")
        )


def _pptx_media_count(payload: bytes) -> int:
    with zipfile.ZipFile(BytesIO(payload), "r") as pptx:
        return len([name for name in pptx.namelist() if name.startswith("ppt/media/")])


def test_real_user_prompt_keeps_media_baseline_without_public_internal_label() -> None:
    result = SlidesService().generate_deck(REAL_USER_PROMPT)

    assert result.slide_count == 6
    assert result.planning_metadata is not None
    assert result.planning_metadata["requested_slide_count"] == 6

    assert any(slide.image_specs for slide in result.plan.slides)
    assert any(slide.media_assets for slide in result.plan.slides)
    assert _pptx_media_count(result.artifact_content) >= 1
    assert all(asset.source_label is None for slide in result.plan.slides for asset in slide.media_assets)

    pptx_text = _pptx_xml(result.artifact_content)
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in pptx_text
