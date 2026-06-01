from __future__ import annotations

from backend.app.services.slides_service import (
    SOURCE_IMAGE_SELECTION_SCHEMA_VERSION,
    SourceImageSlideRequest,
    sample_source_image_selection_report,
    select_source_images_for_slides,
)
from backend.app.services.slides_service.source_asset_registry import StoredSourceAsset
from backend.app.services.slides_service.template_brand_profile import sample_template_brand_profile_report


def _stored_image(
    *,
    asset_id: str = "market_chart_image",
    source_id: str = "uploaded_market_report",
    package_path: str = "ppt/media/market_chart.png",
    storage_uri: str = "source-asset://uploaded_market_report/market_chart_image",
    provenance_ref: str = "uploaded_market_report#slide:2#image:market_chart",
    checksum: str = "a" * 64,
    mime_type: str = "image/png",
    width_px: int = 1280,
    height_px: int = 720,
) -> StoredSourceAsset:
    return StoredSourceAsset(
        registry_entry_id=f"registry_{asset_id}",
        asset_id=asset_id,
        source_id=source_id,
        asset_type="image",
        source_package_path=package_path,
        relative_path=f"{source_id}/assets/{asset_id}.png",
        storage_uri=storage_uri,
        provenance_ref=provenance_ref,
        checksum_sha256=checksum,
        size_bytes=128_000,
        mime_type=mime_type,
        slide_number=2,
        width_px=width_px,
        height_px=height_px,
    )


def test_kr7j_sample_source_image_selection_is_ready() -> None:
    report = sample_source_image_selection_report()

    assert report["schema_version"] == SOURCE_IMAGE_SELECTION_SCHEMA_VERSION
    assert report["status"] == "ready"
    assert report["source_image_selection_implemented"] is True
    assert report["source_images_only_enforced"] is True
    assert report["selected_image_count"] == 1
    assert report["candidate_count"] >= 2
    assert report["slide_bindings"][0]["status"] == "selected"
    assert report["slide_bindings"][0]["citation"]
    assert report["slide_bindings"][1]["status"] == "typographic_fallback"
    assert report["generated_images_allowed"] is False
    assert report["random_images_allowed"] is False
    assert report["fake_artifacts_allowed"] is False
    assert report["inline_image_payloads_allowed"] is False
    assert report["renderer_runtime_changed"] is False
    assert report["visual_qa_executed"] is False
    assert report["kimi_level_quality_claimed"] is False


def test_kr7j_selects_only_uploaded_source_assets_with_citation() -> None:
    slides = [
        SourceImageSlideRequest(
            slide_id="s_market",
            role="data",
            title="Market chart",
            intent_query="market chart evidence",
            expected_terms=("market", "chart"),
            requires_image=True,
        )
    ]

    result = select_source_images_for_slides(slides, source_assets=[_stored_image()])
    payload = result.as_dict()

    assert payload["status"] == "ready"
    assert payload["selected_image_count"] == 1
    binding = payload["slide_bindings"][0]
    assert binding["status"] == "selected"
    assert binding["selected_image_id"] == "source_image_market_chart_image"
    assert binding["citation"] == "uploaded_market_report#slide:2#image:market_chart"
    candidate = payload["candidates"][0]
    assert candidate["source_kind"] == "uploaded_document"
    assert candidate["source_backed"] is True
    assert candidate["generated_asset"] is False


def test_kr7j_reuses_template_media_without_claiming_generation() -> None:
    slides = [
        {
            "slide_id": "s_template",
            "role": "cover",
            "title": "Template image",
            "intent_query": "template media brand",
            "expected_terms": ["template", "media"],
        }
    ]

    result = select_source_images_for_slides(slides, template_profile=sample_template_brand_profile_report())
    payload = result.as_dict()

    assert payload["status"] == "ready"
    assert payload["selected_image_count"] == 1
    binding = payload["slide_bindings"][0]
    assert binding["status"] == "selected"
    assert binding["citation"].startswith("kr7i_sample_template#ppt/media/image1.png")
    candidate = payload["candidates"][0]
    assert candidate["source_kind"] == "uploaded_template"
    assert candidate["generated_asset"] is False


def test_kr7j_typographic_fallback_when_no_relevant_source_image_exists() -> None:
    slides = [
        SourceImageSlideRequest(
            slide_id="s_roadmap",
            role="roadmap",
            title="Roadmap",
            intent_query="roadmap milestones",
            expected_terms=("roadmap", "milestones"),
            requires_image=True,
        )
    ]

    result = select_source_images_for_slides(slides, source_assets=[_stored_image()])
    payload = result.as_dict()

    assert payload["status"] == "degraded"
    assert payload["selected_image_count"] == 0
    binding = payload["slide_bindings"][0]
    assert binding["status"] == "typographic_fallback"
    assert binding["selected_image_id"] is None
    assert binding["citation"] is None
    assert binding["fallback_reason"] == "required_image_has_no_relevant_source_asset_typographic_fallback"


def test_kr7j_blocks_external_inline_or_generated_image_candidates() -> None:
    generated = _stored_image(asset_id="generated_placeholder", package_path="generated/placeholder.png")
    external = _stored_image(
        asset_id="external_image",
        package_path="ppt/media/external.png",
        storage_uri="https://example.invalid/external.png",
        provenance_ref="external#image",
        checksum="b" * 64,
    )
    inline = {
        "asset_id": "inline_image",
        "source_id": "uploaded_doc",
        "asset_type": "image",
        "source_package_path": "word/media/inline.png",
        "storage_uri": "source-asset://uploaded_doc/inline_image",
        "provenance_ref": "uploaded_doc#asset:inline",
        "checksum_sha256": "c" * 64,
        "size_bytes": 1234,
        "mime_type": "image/png",
        "content_bytes": b"raw-bytes-must-not-be-public-selection-input",
    }

    result = select_source_images_for_slides(
        [SourceImageSlideRequest(slide_id="s", role="data", title="external image", expected_terms=("external",))],
        source_assets=[generated, external, inline],
    )
    payload = result.as_dict()

    assert payload["status"] == "blocked"
    assert payload["candidate_count"] == 0
    assert any("source asset external_image uses forbidden" in error for error in payload["errors"])
    assert any("not a source-backed reusable image" in error for error in payload["errors"])
    assert payload["generated_images_allowed"] is False
    assert payload["fake_artifacts_allowed"] is False
