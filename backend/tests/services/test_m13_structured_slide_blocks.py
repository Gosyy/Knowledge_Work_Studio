from io import BytesIO
import zipfile

import pytest

from backend.app.services.slides_service.blocks import ChartBlock, TableBlock
from backend.app.services.slides_service.generator import generate_pptx_from_plan
from backend.app.services.slides_service.outline import (
    PlannedSlide,
    PresentationPlan,
    SlideType,
    StoryArcStage,
    build_presentation_plan,
)


def _single_slide_plan(slide: PlannedSlide) -> PresentationPlan:
    return PresentationPlan(
        deck_title=slide.title,
        deck_goal="Test structured slide blocks.",
        audience="general_business",
        tone="clear_professional",
        target_slide_count=1,
        story_arc=(slide.story_arc_stage,),
        slides=(slide,),
    )


def test_m13_planner_attaches_structured_blocks_for_business_slide_types() -> None:
    plan = build_presentation_plan(
        "Executive opening. Market context. Operating model. Compare options. Delivery timeline. Revenue 10 cost 4 margin 6. Final recommendation."
    )

    comparison_slide = next(slide for slide in plan.slides if slide.slide_type is SlideType.COMPARISON)
    timeline_slide = next(slide for slide in plan.slides if slide.slide_type is SlideType.TIMELINE)
    data_slide = next(slide for slide in plan.slides if slide.slide_type is SlideType.DATA)

    assert any(block.block_type.value == "comparison_block" for block in comparison_slide.blocks)
    assert any(block.block_type.value == "timeline_block" for block in timeline_slide.blocks)
    assert any(block.block_type.value == "table_block" for block in data_slide.blocks)
    assert any(block.block_type.value == "chart_block" for block in data_slide.blocks)
    assert any(block.block_type.value == "business_metric_block" for block in data_slide.blocks)


def test_m13_renders_data_slide_as_real_table_chart_and_metric_shapes() -> None:
    plan = build_presentation_plan(
        "Executive opening. Market context. Operating model. Compare options. Delivery timeline. Revenue 10 cost 4 margin 6. Final recommendation."
    )
    data_slide = next(slide for slide in plan.slides if slide.slide_type is SlideType.DATA)

    payload = generate_pptx_from_plan(_single_slide_plan(data_slide), template_id="default_light")

    with zipfile.ZipFile(BytesIO(payload), "r") as pptx_zip:
        slide_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")

    assert "table_block cell" in slide_xml
    assert "chart_block bar" in slide_xml
    assert "business_metric_block card" in slide_xml
    assert "Structured data summary" in slide_xml
    assert "Evidence weight by signal" in slide_xml


def test_m13_renders_comparison_and_timeline_as_structured_shapes() -> None:
    plan = build_presentation_plan(
        "Executive opening. Market context. Operating model. Compare options. Delivery timeline. Revenue 10 cost 4 margin 6. Final recommendation."
    )
    comparison_slide = next(slide for slide in plan.slides if slide.slide_type is SlideType.COMPARISON)
    timeline_slide = next(slide for slide in plan.slides if slide.slide_type is SlideType.TIMELINE)

    comparison_payload = generate_pptx_from_plan(_single_slide_plan(comparison_slide), template_id="default_light")
    timeline_payload = generate_pptx_from_plan(_single_slide_plan(timeline_slide), template_id="default_light")

    with zipfile.ZipFile(BytesIO(comparison_payload), "r") as pptx_zip:
        comparison_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")
    with zipfile.ZipFile(BytesIO(timeline_payload), "r") as pptx_zip:
        timeline_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")

    assert "comparison_block left" in comparison_xml
    assert "comparison_block right" in comparison_xml
    assert "timeline_block line" in timeline_xml
    assert "timeline_block marker" in timeline_xml


def test_m13_table_and_chart_blocks_fail_loudly_when_invalid() -> None:
    bad_table_slide = PlannedSlide(
        slide_id="bad_table",
        slide_type=SlideType.DATA,
        story_arc_stage=StoryArcStage.ANALYSIS,
        title="Bad table",
        bullets=("bad",),
        layout_hint="data_summary",
        blocks=(
            TableBlock(
                block_id="bad_table_block",
                columns=("A", "B"),
                rows=(("only-one-cell",),),
            ),
        ),
    )

    with pytest.raises(ValueError, match="expected 2"):
        generate_pptx_from_plan(_single_slide_plan(bad_table_slide), template_id="default_light")

    bad_chart_slide = PlannedSlide(
        slide_id="bad_chart",
        slide_type=SlideType.DATA,
        story_arc_stage=StoryArcStage.ANALYSIS,
        title="Bad chart",
        bullets=("bad",),
        layout_hint="data_summary",
        blocks=(
            ChartBlock(
                block_id="bad_chart_block",
                title="Bad chart",
                categories=("A", "B"),
                values=(1.0,),
            ),
        ),
    )

    with pytest.raises(ValueError, match="categories"):
        generate_pptx_from_plan(_single_slide_plan(bad_chart_slide), template_id="default_light")
