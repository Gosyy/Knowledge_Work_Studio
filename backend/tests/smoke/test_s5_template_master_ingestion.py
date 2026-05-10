from __future__ import annotations

from backend.app.services.slides_service.template_master_ingestion import (
    build_template_layout_mappings,
    extract_local_template_master_metadata,
    template_master_ingestion_report,
    validate_local_template_reference,
    validate_template_master_ingestion,
)


def test_s5_template_master_ingestion_report_ready() -> None:
    report = template_master_ingestion_report()
    assert report["status"] == "ready"
    assert report["template_master_ingestion_completed_by_s5"] is True
    assert report["local_template_registry_count"] >= 3
    assert report["slide_master_metadata_extracted_by_s5"] is True
    assert report["s3_archetype_to_template_layout_mapping_ready_by_s5"] is True
    assert report["s4_native_visual_to_template_layout_mapping_ready_by_s5"] is True
    assert report["kimi_level_claimed_by_s5"] is False
    assert report["server3_local_intranet_route_verified_by_s5"] is False


def test_s5_extracts_local_template_master_metadata() -> None:
    metadata = extract_local_template_master_metadata()
    assert "business_clean" in metadata
    for template_id, meta in metadata.items():
        assert meta.template_id == template_id
        assert meta.theme_name
        assert meta.font_family
        assert meta.accent_color
        assert len(meta.layout_ids) >= 5
        assert meta.source == "local_builtin_registry"
        assert meta.external_discovery_allowed is False
        assert meta.public_internet_required is False


def test_s5_maps_s3_archetypes_and_s4_native_visuals_to_template_layouts() -> None:
    mappings = build_template_layout_mappings()
    assert len(mappings) >= 30
    mapped_pairs = {(mapping.deck_mode_id, mapping.slide_archetype) for mapping in mappings}
    assert ("decision_matrix_deck", "option_matrix") in mapped_pairs
    assert ("architecture_review_deck", "topology_map") in mapped_pairs
    assert ("architecture_review_deck", "failure_modes_operator_gates") in mapped_pairs
    assert ("long_document_explainer", "evidence_package") in mapped_pairs
    assert all(mapping.template_id_required for mapping in mappings)
    assert all(mapping.provenance_required for mapping in mappings)
    assert all(mapping.editable_pptx_required for mapping in mappings)
    assert not validate_template_master_ingestion()


def test_s5_rejects_external_template_references() -> None:
    assert not validate_local_template_reference("business_clean")
    for value in ("https://example.com/theme.pptx", "s3://bucket/theme.pptx", "../theme.pptx", "/tmp/theme.pptx"):
        assert validate_local_template_reference(value)
