from __future__ import annotations

from dataclasses import replace

from backend.app.services.slides_service import (
    ImageFitMode,
    SlideMediaAsset,
    build_presentation_plan,
    build_source_grounded_plan,
    deserialize_presentation_plan,
    serialize_presentation_plan,
)


def test_o1_plan_snapshot_round_trips_blocks_images_media_refs_and_source_grounding() -> None:
    base_plan = build_presentation_plan(
        "Executive opening. Market context. Operating model. Compare options. Delivery timeline. Revenue 10 cost 4 margin 6. Final recommendation.",
        min_slides=7,
        max_slides=7,
    )
    grounded = build_source_grounded_plan(
        base_plan,
        source_text="Alpha evidence. Beta evidence. Gamma evidence.",
        source_refs=(
            {
                "kind": "stored_file",
                "source_id": "sf_o1_source",
                "role": "primary_source",
                "source_file_id": "sf_o1_source",
                "derived_content_id": "dcon_o1",
            },
        ),
    ).plan

    media_asset = SlideMediaAsset(
        media_id="media_o1",
        filename="o1.png",
        content_type="image/png",
        data=b"binary-image-data-that-must-not-enter-snapshot-json",
        width_px=128,
        height_px=72,
        fit_mode=ImageFitMode.CONTAIN,
        alt_text="O1 media",
        caption="O1 media caption",
        source_label="generated",
        stored_file_id="sfimg_o1",
        storage_uri="local://unsafe/internal/path.png",
    )
    slides = list(grounded.slides)
    slides[2] = replace(slides[2], media_assets=(media_asset,))
    plan = replace(grounded, slides=tuple(slides))

    payload = serialize_presentation_plan(plan)

    assert payload["schema_version"] == 1
    assert "binary-image-data-that-must-not-enter-snapshot-json" not in str(payload)
    assert "local://unsafe/internal/path.png" not in str(payload)

    restored = deserialize_presentation_plan(payload)

    assert serialize_presentation_plan(restored) == payload
    assert restored.deck_title == plan.deck_title
    assert restored.slides[2].slide_id == "slide_003"
    assert restored.slides[2].media_assets[0].stored_file_id == "sfimg_o1"
    assert restored.slides[2].media_assets[0].data == b""
    assert restored.slides[2].citations[0].source_id == "sf_o1_source"
    assert restored.slides[2].source_notes
    assert any(block.block_type.value == "table_block" for slide in restored.slides for block in slide.blocks)
    assert any(block.block_type.value == "chart_block" for slide in restored.slides for block in slide.blocks)
