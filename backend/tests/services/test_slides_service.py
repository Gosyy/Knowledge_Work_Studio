import zipfile
from io import BytesIO

from backend.app.services.slides_service import SlidesService, build_slides_outline


def test_slides_service_generates_valid_openxml_pptx_payload() -> None:
    service = SlidesService()

    result = service.generate_deck("Intro slide. Problem statement. Proposed solution.")

    assert result.slide_count == 5
    assert result.summary_text == "Generated 5 slide(s)."
    assert result.artifact_content[:2] == b"PK"

    with zipfile.ZipFile(BytesIO(result.artifact_content), "r") as pptx_zip:
        names = set(pptx_zip.namelist())
        slide_entries = [name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
        content_types = pptx_zip.read("[Content_Types].xml").decode("utf-8")
        presentation_xml = pptx_zip.read("ppt/presentation.xml").decode("utf-8")
        first_slide_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")

    assert len(slide_entries) == 5
    assert "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml" in content_types
    assert "application/vnd.openxmlformats-officedocument.presentationml.slide+xml" in content_types
    assert "ppt/_rels/presentation.xml.rels" in names
    assert "ppt/slideMasters/slideMaster1.xml" in names
    assert "ppt/slideLayouts/slideLayout1.xml" in names
    assert "ppt/theme/theme1.xml" in names
    assert "<p:sldIdLst>" in presentation_xml
    assert "Intro slide" in first_slide_xml
    assert not any(name.endswith(".txt") for name in names)


def test_outline_builder_is_deterministic_and_bounded() -> None:
    outline = build_slides_outline("A. B. C. D. E. F. G. H. I. J. K.")

    assert len(outline) == 10
    assert outline[0].title.startswith("Slide 1:")
