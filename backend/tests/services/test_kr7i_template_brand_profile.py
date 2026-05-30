from __future__ import annotations

from pathlib import Path

from backend.app.services.slides_service import (
    TEMPLATE_BRAND_PROFILE_SCHEMA_VERSION,
    build_sample_template_pptx_bytes,
    inspect_pptx_template_brand_profile,
    inspect_pptx_template_brand_profile_bytes,
    sample_template_brand_profile_report,
    validate_template_reference,
)


def test_kr7i_sample_template_brand_profile_is_ready() -> None:
    report = sample_template_brand_profile_report()

    assert report["schema_version"] == TEMPLATE_BRAND_PROFILE_SCHEMA_VERSION
    assert report["phase"] == "KR-7I template and brand understanding"
    assert report["status"] == "ready"
    assert report["template_source_kind"] == "uploaded_pptx_template"
    assert report["template_profile_built"] is True
    assert report["template_style_understanding_implemented"] is True
    assert report["template_content_copied"] is False
    assert report["production_layout_engine_implemented"] is False
    assert report["renderer_runtime_changed"] is False
    assert report["visual_qa_executed"] is False
    assert report["kimi_level_quality_claimed"] is False

    assert report["slide_size"]["width_emu"] == 12_192_000
    assert report["slide_size"]["height_emu"] == 6_858_000
    assert report["slide_size"]["preset"] == "wide"
    assert report["theme"]["major_font"] == "Aptos Display"
    assert report["theme"]["minor_font"] == "Aptos"
    assert report["theme"]["color_tokens"]["accent1"] == "#2563EB"
    assert report["slide_masters_count"] == 1
    assert report["slide_layout_count"] == 3
    assert report["media_asset_count"] == 1
    assert report["media_assets"][0]["width_px"] == 1
    assert report["media_assets"][0]["height_px"] == 1
    assert report["media_assets"][0]["reused_as_generated_asset"] is False
    assert report["role_layout_family_map"]["cover"] == "cover"
    assert report["role_layout_family_map"]["roadmap"] == "timeline"
    assert report["role_layout_family_map"]["data"] == "data"
    assert "no_template_clone_rewrite_mode" in report["non_goals"]


def test_kr7i_rejects_invalid_or_external_template_references() -> None:
    assert validate_template_reference("brand-template.pptx") == []
    assert validate_template_reference("https://example.com/brand.pptx")
    assert validate_template_reference("../brand.pptx")
    assert validate_template_reference("/tmp/brand.pptx")


def test_kr7i_can_inspect_template_from_local_pptx_path(tmp_path: Path) -> None:
    template_path = tmp_path / "kr7i-template.pptx"
    template_path.write_bytes(build_sample_template_pptx_bytes())

    result = inspect_pptx_template_brand_profile(template_path, template_id="local_kr7i_template")
    report = result.as_dict()

    assert report["status"] == "ready"
    assert report["template_id"] == "local_kr7i_template"
    assert report["template_file_name"] == "kr7i-template.pptx"
    assert report["template_content_copied"] is False
    assert report["slide_layouts"][0]["layout_family"] == "cover"
    assert {layout["layout_family"] for layout in report["slide_layouts"]} >= {"cover", "title_content", "comparison"}


def test_kr7i_fails_closed_for_non_pptx_bytes() -> None:
    result = inspect_pptx_template_brand_profile_bytes(b"not a pptx", template_file_name="bad.pptx")
    report = result.as_dict()

    assert report["status"] == "blocked"
    assert report["template_profile_built"] is False
    assert report["template_style_understanding_implemented"] is False
    assert report["errors"]
