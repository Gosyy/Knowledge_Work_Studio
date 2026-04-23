import zipfile
from io import BytesIO

from backend.app.services.slides_service import SlidesService, SlideType, StoryArcStage, build_presentation_plan, build_slides_outline


def test_slides_service_generates_valid_openxml_pptx_payload() -> None:
    service = SlidesService()

    result = service.generate_deck("Intro slide. Problem statement. Proposed solution.")

    assert result.slide_count == 5
    assert result.summary_text == "Generated 5 slide(s)."
    assert result.outline[0].title.startswith("Slide 1:")
    assert result.plan.slides[0].slide_type is SlideType.TITLE
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


def test_presentation_planner_returns_typed_plan_and_explicit_story_arc() -> None:
    plan = build_presentation_plan(
        "Opening framing. Market context. Options comparison. Delivery sequence. KPI summary. Final recommendation."
    )

    assert plan.target_slide_count == len(plan.slides)
    assert plan.slides[0].slide_type is SlideType.TITLE
    assert plan.slides[1].slide_type is SlideType.SECTION
    assert plan.slides[-1].slide_type is SlideType.CONCLUSION
    assert plan.story_arc[0] is StoryArcStage.OPENING
    assert plan.story_arc[-1] is StoryArcStage.CLOSE
    assert {slide.slide_type for slide in plan.slides} >= {SlideType.TITLE, SlideType.SECTION, SlideType.CONCLUSION}


def test_presentation_planner_bounds_bullets_and_slide_count_deterministically() -> None:
    text = (
        "This sentence contains many words intended to force bullet chunking across the planning layer with deterministic boundaries. "
        "Another sentence expands the body material for the deck. "
        "A final sentence closes the presentation strongly."
    )

    first_plan = build_presentation_plan(text, min_slides=5, max_slides=6)
    second_plan = build_presentation_plan(text, min_slides=5, max_slides=6)

    assert first_plan == second_plan
    assert 5 <= len(first_plan.slides) <= 6
    for slide in first_plan.slides:
        assert len(slide.bullets) <= 3
        for bullet in slide.bullets:
            assert len(bullet.split()) <= 12


def test_outline_builder_remains_compatibility_bridge() -> None:
    outline = build_slides_outline("A. B. C. D. E. F. G. H. I. J. K.")

    assert len(outline) == 10
    assert outline[0].title.startswith("Slide 1:")
    assert outline[-1].title.startswith("Slide 10:")
