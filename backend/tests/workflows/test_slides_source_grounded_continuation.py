from __future__ import annotations

import json

from backend.app.services.slides_service.source_grounded_continuation import (
    build_source_grounded_slides_bundle,
    sample_source_refs,
    sample_source_text,
)


def test_kr6a_source_grounded_slides_bundle_covers_every_slide() -> None:
    bundle = build_source_grounded_slides_bundle(source_text=sample_source_text(), source_refs=sample_source_refs())

    assert bundle.status == "ready", bundle.quality.issues
    assert len(bundle.grounding.plan.slides) >= 5
    assert len(bundle.grounding.citations) == len(bundle.grounding.plan.slides)
    assert all(slide.citations for slide in bundle.grounding.plan.slides)
    assert all(slide.source_notes for slide in bundle.grounding.plan.slides)


def test_kr6a_source_grounded_slides_bundle_artifacts_are_traceable() -> None:
    bundle = build_source_grounded_slides_bundle(source_text=sample_source_text(), source_refs=sample_source_refs())

    assert {
        "slide_plan.json",
        "citation_manifest.json",
        "source_evidence_manifest.json",
        "quality_report.json",
        "artifact_manifest.json",
    }.issubset(set(bundle.artifact_names()))
    citation_manifest = json.loads(bundle.text_artifact("citation_manifest.json"))
    evidence_manifest = json.loads(bundle.text_artifact("source_evidence_manifest.json"))
    citation_ids = {item["citation_id"] for item in citation_manifest["citations"]}
    evidence_ids = {item["citation_id"] for item in evidence_manifest["evidence_items"]}
    assert citation_ids == evidence_ids


def test_kr6a_source_grounding_fails_closed_without_sources() -> None:
    bundle = build_source_grounded_slides_bundle(source_text=sample_source_text(), source_refs=())

    assert bundle.status == "not_ready"
    assert "source_refs_present" in bundle.quality.issues
    assert "all_slides_have_citations" in bundle.quality.issues
