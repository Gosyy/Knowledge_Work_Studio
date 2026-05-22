from io import BytesIO
import zipfile

from backend.app.services.slides_service.service import SlidesService

PROMPT = (
    "Сгенерируй презентацию на 6 слайдов на тему: как компания может внедрить "
    "внутреннюю систему Knowledge Work Studio для работы с документами, таблицами, "
    "PDF, презентациями и проверяемыми артефактами. Стиль: деловой, понятно для руководителя."
)

FORBIDDEN = [
    "Additional insight",
    "Local deterministic slide image generation",
    "Key points",
    "Option A",
    "Current path",
    "Step 1",
]


def _extract_text(payload: bytes) -> list[str]:
    with zipfile.ZipFile(BytesIO(payload), "r") as pptx:
        xml = "\n".join(
            pptx.read(name).decode("utf-8", errors="replace")
            for name in pptx.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
    return [chunk.strip() for chunk in xml.split(">") if chunk.strip()]


def test_pptx_public_text_quality_regression() -> None:
    result = SlidesService().generate_deck(PROMPT, source_mode="prompt_only")
    assert result.slide_count == 6
    text_blocks = _extract_text(result.artifact_content)
    joined = "\n".join(text_blocks)
    for bad in FORBIDDEN:
        assert bad not in joined
    assert "Сгенерируй презентацию" not in joined
    titles = [item.title for item in result.outline]
    assert len(set(titles)) == 6
    for title in titles:
        assert len(title.strip()) > 4
    for slide in result.outline:
        assert 2 <= len(slide.bullets) <= 5
