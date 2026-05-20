from __future__ import annotations

from backend.app.services.slides_service.render_visual_qa_bundle import sample_slides_render_visual_qa_bundle


def test_kr6b_render_visual_qa_bundle_contains_primary_and_independent_renders() -> None:
    bundle = sample_slides_render_visual_qa_bundle()
    slide_count = len(bundle.source_grounded.grounding.plan.slides)

    assert bundle.status == "ready", bundle.quality.issues
    assert slide_count >= 5
    assert len([record for record in bundle.render_artifacts if not record.independent]) == slide_count
    assert len([record for record in bundle.render_artifacts if record.independent]) == slide_count
    assert all(bundle.artifacts[record.path].startswith(b"\x89PNG\r\n\x1a\n") for record in bundle.render_artifacts)


def test_kr6b_geometry_report_covers_every_source_grounded_slide() -> None:
    bundle = sample_slides_render_visual_qa_bundle()
    slide_ids = {slide.slide_id for slide in bundle.source_grounded.grounding.plan.slides}
    geometry_ids = {record.slide_id for record in bundle.geometry}

    assert slide_ids == geometry_ids
    assert all(record.boxes_within_slide for record in bundle.geometry)
    assert all(record.citation_box_reserved for record in bundle.geometry)
