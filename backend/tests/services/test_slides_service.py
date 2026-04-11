import zipfile
from io import BytesIO

from backend.app.services.slides_service import SlidesService, build_slides_outline


def test_slides_service_generates_outline_first_pptx_payload() -> None:
    service = SlidesService()

    result = service.generate_deck("Intro slide. Problem statement. Proposed solution.")

    assert result.slide_count == 5
    assert result.summary_text == "Generated 5 slide(s)."
    assert result.artifact_content[:2] == b"PK"

    with zipfile.ZipFile(BytesIO(result.artifact_content), "r") as pptx_zip:
        slide_entries = [name for name in pptx_zip.namelist() if name.startswith("ppt/slides/slide")]
    assert len(slide_entries) == 5


def test_outline_builder_is_deterministic_and_bounded() -> None:
    outline = build_slides_outline("A. B. C. D. E. F. G. H. I. J. K.")

    assert len(outline) == 10
    assert outline[0].title.startswith("Slide 1:")
