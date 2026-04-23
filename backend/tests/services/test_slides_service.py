import base64
import zipfile
from io import BytesIO

import pytest

from backend.app.services.slides_service import (
    ImageFitMode,
    PlannedSlide,
    PresentationPlan,
    SlideMediaAsset,
    SlidesService,
    SlideType,
    StoryArcStage,
    build_presentation_plan,
    build_slides_outline,
    generate_pptx_from_plan,
    get_template_registry,
    resolve_layout_for_slide,
)

_SMALL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WnWkQAAAABJRU5ErkJggg=="
)


def test_slides_service_generates_valid_openxml_pptx_payload() -> None:
    service = SlidesService()

    result = service.generate_deck("Intro slide. Problem statement. Proposed solution.")

    assert result.slide_count == 5
    assert result.summary_text == "Generated 5 slide(s)."
    assert result.outline[0].title.startswith("Slide 1:")
    assert result.plan.slides[0].slide_type is SlideType.TITLE
    assert result.template_id == "default_light"
    assert result.artifact_content[:2] == b"PK"

    with zipfile.ZipFile(BytesIO(result.artifact_content), "r") as pptx_zip:
        names = set(pptx_zip.namelist())
        slide_entries = [name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
        content_types = pptx_zip.read("[Content_Types].xml").decode("utf-8")
        presentation_xml = pptx_zip.read("ppt/presentation.xml").decode("utf-8")
        first_slide_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")
        theme_xml = pptx_zip.read("ppt/theme/theme1.xml").decode("utf-8")

    assert len(slide_entries) == 5
    assert "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml" in content_types
    assert "application/vnd.openxmlformats-officedocument.presentationml.slide+xml" in content_types
    assert "ppt/_rels/presentation.xml.rels" in names
    assert "ppt/slideMasters/slideMaster1.xml" in names
    assert "ppt/slideLayouts/slideLayout1.xml" in names
    assert "ppt/theme/theme1.xml" in names
    assert "<p:sldIdLst>" in presentation_xml
    assert "Intro slide" in first_slide_xml
    assert "KW Studio Light" in theme_xml
    assert not any(name.endswith(".txt") for name in names)
    assert not any(name.startswith("ppt/media/") for name in names)


def test_presentation_planner_returns_typed_plan_and_explicit_story_arc() -> None:
    plan = build_presentation_plan(
        "Opening framing. Market context. Options comparison. Delivery sequence. KPI summary. Final recommendation. Supporting appendix note."
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


def test_template_registry_exposes_multiple_templates() -> None:
    registry = get_template_registry()

    assert {"default_light", "default_dark", "business_clean"} <= set(registry)
    assert registry["default_light"].background_color == "FFFFFF"
    assert registry["default_dark"].background_color == "1F1F1F"
    assert registry["business_clean"].font_family == "Aptos"
    assert registry["default_light"].layouts["content_with_visual"].image_placeholders


def test_layout_resolver_uses_slide_type_and_layout_hint() -> None:
    plan = build_presentation_plan(
        "Opening framing. Market context. Options comparison. Delivery sequence. KPI summary. Final recommendation. Supporting appendix note."
    )

    comparison_slide = next(slide for slide in plan.slides if slide.slide_type is SlideType.COMPARISON)
    data_slide = next(slide for slide in plan.slides if slide.slide_type is SlideType.DATA)

    comparison_layout = resolve_layout_for_slide(comparison_slide, template_id="default_light")
    data_layout = resolve_layout_for_slide(data_slide, template_id="default_light")

    assert comparison_layout.layout.layout_id == "two_column_comparison"
    assert len(comparison_layout.layout.body_boxes) == 2
    assert data_layout.layout.layout_id == "data_summary"
    assert len(data_layout.layout.body_boxes) == 1


def test_slides_service_can_render_with_branded_template_selection() -> None:
    service = SlidesService()

    result = service.generate_deck(
        "Company context. Business problem. Alternatives. Delivery timing. KPI outcomes. Final recommendation.",
        template_id="business_clean",
    )

    assert result.template_id == "business_clean"
    assert result.summary_text == "Generated 6 slide(s) with template 'business_clean'."

    with zipfile.ZipFile(BytesIO(result.artifact_content), "r") as pptx_zip:
        theme_xml = pptx_zip.read("ppt/theme/theme1.xml").decode("utf-8")
        first_slide_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")

    assert "KW Studio Business" in theme_xml
    assert "Aptos" in theme_xml
    assert "F7F9FC" in first_slide_xml


def test_generator_embeds_media_assets_into_pptx_with_valid_relationships() -> None:
    slide = PlannedSlide(
        slide_id="slide_media_001",
        slide_type=SlideType.CONTENT,
        story_arc_stage=StoryArcStage.ANALYSIS,
        title="Visual slide",
        bullets=("One supporting point", "Second supporting point"),
        layout_hint="content_with_visual",
        media_assets=(
            SlideMediaAsset(
                media_id="img_001",
                filename="chart.png",
                content_type="image/png",
                data=_SMALL_PNG,
                width_px=1600,
                height_px=900,
                fit_mode=ImageFitMode.CONTAIN,
                alt_text="Embedded chart",
            ),
        ),
    )
    plan = PresentationPlan(
        deck_title="Visual deck",
        deck_goal="Test media embedding.",
        audience="general_business",
        tone="clear_professional",
        target_slide_count=1,
        story_arc=(StoryArcStage.ANALYSIS,),
        slides=(slide,),
    )

    payload = generate_pptx_from_plan(plan, template_id="default_light")

    with zipfile.ZipFile(BytesIO(payload), "r") as pptx_zip:
        names = set(pptx_zip.namelist())
        content_types = pptx_zip.read("[Content_Types].xml").decode("utf-8")
        slide_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")
        rels_xml = pptx_zip.read("ppt/slides/_rels/slide1.xml.rels").decode("utf-8")
        media_bytes = pptx_zip.read("ppt/media/image1.png")

    assert "ppt/media/image1.png" in names
    assert media_bytes == _SMALL_PNG
    assert 'Extension="png" ContentType="image/png"' in content_types
    assert 'relationships/image' in rels_xml
    assert '../media/image1.png' in rels_xml
    assert '<p:pic>' in slide_xml
    assert 'r:embed="rId2"' in slide_xml
    assert 'descr="Embedded chart"' in slide_xml


def test_generator_applies_cover_fit_with_src_rect_crop() -> None:
    slide = PlannedSlide(
        slide_id="slide_media_002",
        slide_type=SlideType.TITLE,
        story_arc_stage=StoryArcStage.OPENING,
        title="Cover visual",
        bullets=("Headline",),
        layout_hint="title_with_visual",
        media_assets=(
            SlideMediaAsset(
                media_id="img_002",
                filename="cover.png",
                content_type="image/png",
                data=_SMALL_PNG,
                width_px=1600,
                height_px=400,
                fit_mode=ImageFitMode.COVER,
            ),
        ),
    )
    plan = PresentationPlan(
        deck_title="Cover deck",
        deck_goal="Test cover cropping.",
        audience="general_business",
        tone="clear_professional",
        target_slide_count=1,
        story_arc=(StoryArcStage.OPENING,),
        slides=(slide,),
    )

    payload = generate_pptx_from_plan(plan, template_id="default_light")

    with zipfile.ZipFile(BytesIO(payload), "r") as pptx_zip:
        slide_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")

    assert '<a:srcRect ' in slide_xml
    assert ' l="' in slide_xml or ' t="' in slide_xml


def test_generator_fails_honestly_when_layout_has_no_image_placeholder() -> None:
    slide = PlannedSlide(
        slide_id="slide_media_003",
        slide_type=SlideType.CONTENT,
        story_arc_stage=StoryArcStage.ANALYSIS,
        title="Broken visual layout",
        bullets=("Only text layout",),
        layout_hint="title_and_bullets",
        media_assets=(
            SlideMediaAsset(
                media_id="img_003",
                filename="broken.png",
                content_type="image/png",
                data=_SMALL_PNG,
                width_px=800,
                height_px=600,
            ),
        ),
    )
    plan = PresentationPlan(
        deck_title="Broken visual deck",
        deck_goal="Test honest failure.",
        audience="general_business",
        tone="clear_professional",
        target_slide_count=1,
        story_arc=(StoryArcStage.ANALYSIS,),
        slides=(slide,),
    )

    with pytest.raises(ValueError, match="does not define image placeholders"):
        generate_pptx_from_plan(plan, template_id="default_light")
