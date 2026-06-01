from __future__ import annotations

from backend.app.services.slides_service import (
    PROFESSIONAL_LAYOUT_SCHEMA_VERSION,
    ProfessionalLayoutSlideRequest,
    sample_professional_layout_report,
    solve_professional_layout,
)
from backend.app.services.slides_service.data_backed_charts import DataChartRequest, bind_data_backed_charts
from backend.app.services.slides_service.offline_source_ingestion import SourceTableCandidate
from backend.app.services.slides_service.source_image_selection import SourceImageSlideRequest, select_source_images_for_slides
from backend.app.services.slides_service.source_asset_registry import StoredSourceAsset
from backend.app.services.slides_service.template_brand_profile import sample_template_brand_profile_report


def _source_image() -> StoredSourceAsset:
    return StoredSourceAsset(
        registry_entry_id="registry_product_photo",
        asset_id="product_photo",
        source_id="uploaded_brand_deck",
        asset_type="image",
        source_package_path="ppt/media/product_photo.png",
        relative_path="uploaded_brand_deck/assets/product_photo.png",
        storage_uri="source-asset://uploaded_brand_deck/product_photo",
        provenance_ref="uploaded_brand_deck#slide:3#image:product_photo",
        checksum_sha256="b" * 64,
        size_bytes=256_000,
        mime_type="image/png",
        slide_number=3,
        width_px=1600,
        height_px=900,
    )


def _revenue_table() -> SourceTableCandidate:
    return SourceTableCandidate(
        table_id="revenue_table",
        source_id="uploaded_finance_workbook",
        rows=[
            ["Quarter", "Revenue", "Cost"],
            ["Q1", "120", "75"],
            ["Q2", "135", "80"],
            ["Q3", "160", "92"],
            ["Q4", "172", "101"],
        ],
        provenance_ref="uploaded_finance_workbook#xlsx-sheet:1!A1:C5",
        caption="Quarterly revenue and cost, USD thousands",
        sheet_name="Finance",
    )


def test_kr7l_sample_professional_layout_report_is_ready() -> None:
    report = sample_professional_layout_report()

    assert report["schema_version"] == PROFESSIONAL_LAYOUT_SCHEMA_VERSION
    assert report["phase"] == "KR-7L professional layout engine"
    assert report["status"] in {"ready", "degraded"}
    assert report["professional_layout_engine_implemented"] is True
    assert report["deterministic_layout_solver_implemented"] is True
    assert report["grid_layout_implemented"] is True
    assert report["typographic_scale_implemented"] is True
    assert report["text_fitting_implemented"] is True
    assert report["overlap_detection_implemented"] is True
    assert report["contrast_density_readability_scores_implemented"] is True
    assert report["title_clipping_prevention_implemented"] is True
    assert report["slide_count"] == 2
    assert report["slide_size"]["width_emu"] > report["slide_size"]["height_emu"]

    for slide in report["slide_plans"]:
        assert slide["overlap_count"] == 0
        assert slide["title_clipped"] is False
        assert 0 <= slide["density_score"] <= 1
        assert 0 <= slide["contrast_score"] <= 1
        assert 0 <= slide["readability_score"] <= 1
        assert 0 <= slide["layout_score"] <= 1
        assert slide["blocks"]

    assert report["native_pptx_layout_mapping_implemented"] is False
    assert report["renderer_runtime_changed"] is False
    assert report["rendered_png_qa_executed"] is False
    assert report["visual_qa_executed"] is False
    assert report["production_layout_claimed"] is False
    assert report["kimi_level_quality_claimed"] is False
    assert "no_renderer_runtime_mapping" in report["non_goals"]


def test_kr7l_solves_content_with_visual_using_source_image_binding() -> None:
    image_result = select_source_images_for_slides(
        [
            SourceImageSlideRequest(
                slide_id="s_visual",
                role="content",
                title="Product visual",
                intent_query="product photo",
                expected_terms=("product", "photo"),
                requires_image=True,
            )
        ],
        source_assets=[_source_image()],
    )

    result = solve_professional_layout(
        [
            ProfessionalLayoutSlideRequest(
                slide_id="s_visual",
                role="content",
                title="Product visual",
                body_items=("Use only source-backed media.", "Keep title and body readable."),
                layout_family_hint="content_with_visual",
                requires_image=True,
            )
        ],
        template_profile=sample_template_brand_profile_report(),
        source_image_selection=image_result,
    )
    report = result.as_dict()

    assert report["status"] == "ready"
    slide = report["slide_plans"][0]
    assert slide["overlap_count"] == 0
    assert slide["title_clipped"] is False
    image_blocks = [block for block in slide["blocks"] if block["block_type"] == "image"]
    assert len(image_blocks) == 1
    assert image_blocks[0]["evidence_ref"] == "uploaded_brand_deck#slide:3#image:product_photo"


def test_kr7l_solves_data_summary_using_data_backed_chart_binding() -> None:
    chart_result = bind_data_backed_charts(
        [
            DataChartRequest(
                slide_id="s_data",
                block_id="s_data_chart",
                role="data",
                title="Quarterly revenue chart",
                intent_query="quarter revenue cost",
                chart_type="line",
                expected_terms=("quarter", "revenue", "cost"),
                requires_chart=True,
            )
        ],
        source_tables=[_revenue_table()],
    )

    report = solve_professional_layout(
        [
            ProfessionalLayoutSlideRequest(
                slide_id="s_data",
                role="data",
                title="Quarterly revenue chart",
                body_items=("Revenue increased every quarter.",),
                layout_family_hint="data_summary",
                requires_chart=True,
            )
        ],
        template_profile=sample_template_brand_profile_report(),
        data_backed_charts=chart_result,
    ).as_dict()

    assert report["status"] == "ready"
    blocks = report["slide_plans"][0]["blocks"]
    chart_blocks = [block for block in blocks if block["block_type"] == "chart"]
    assert len(chart_blocks) == 1
    assert chart_blocks[0]["evidence_ref"] == "uploaded_finance_workbook#xlsx-sheet:1!A1:C5"
    assert report["native_pptx_layout_mapping_implemented"] is False


def test_kr7l_flags_unselected_required_image_as_degraded_not_fake_success() -> None:
    report = solve_professional_layout(
        [
            ProfessionalLayoutSlideRequest(
                slide_id="s_missing_image",
                role="content",
                title="Missing source image",
                body_items=("Stay typographic when no source image exists.",),
                layout_family_hint="content_with_visual",
                requires_image=True,
            )
        ],
        template_profile=sample_template_brand_profile_report(),
    ).as_dict()

    assert report["status"] == "degraded"
    assert report["slide_plans"][0]["overlap_count"] == 0
    assert any("typographic fallback" in warning for warning in report["warnings"])
    assert report["renderer_runtime_changed"] is False
    assert report["production_layout_claimed"] is False


def test_kr7l_blocks_title_that_cannot_fit_minimum_font() -> None:
    impossible_title = " ".join(["ExtremelyLongUnbreakableTitleToken"] * 80)

    report = solve_professional_layout(
        [
            ProfessionalLayoutSlideRequest(
                slide_id="s_bad_title",
                role="content",
                title=impossible_title,
                body_items=("This title should not be accepted as fitted.",),
            )
        ],
        template_profile=sample_template_brand_profile_report(),
    ).as_dict()

    assert report["status"] == "blocked"
    assert report["slide_plans"][0]["title_clipped"] is True
    assert report["slide_plans"][0]["errors"]
