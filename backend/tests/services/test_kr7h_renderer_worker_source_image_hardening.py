from __future__ import annotations

from copy import deepcopy

from backend.app.services.slides_service import (
    RENDERER_WORKER_SOURCE_IMAGE_HARDENING_SCHEMA_VERSION,
    OfflineEvidenceIndexBuilder,
    OfflineSourceIngestionEngine,
    PresentationIRPlannerFoundation,
    PresentationIRPlannerRequest,
    renderer_worker_source_image_hardening_payload,
    validate_renderer_worker_input_payload,
)


def _source_backed_presentation_ir() -> dict[str, object]:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Retention\n\nCustomer retention improved after support automation.\n\n# Risk\n\nDeployment risk decreased after rollout automation.",
        source_id="src_renderer_kr7h12",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h12",
            title="Support automation results",
            objective="Support automation retention risk",
            slide_count=4,
            required_sections=("retention", "risk"),
            require_evidence=True,
        ),
        index,
    )
    assert result.presentation_ir is not None
    return result.presentation_ir


def test_kr7h12_source_image_hardening_contract_is_guardrail_only() -> None:
    payload = renderer_worker_source_image_hardening_payload()

    assert payload["schema_version"] == RENDERER_WORKER_SOURCE_IMAGE_HARDENING_SCHEMA_VERSION
    assert payload["status"] == "ready"
    assert payload["source_image_hardening_implemented"] is True
    assert payload["source_images_only_enforced"] is True
    assert payload["generated_images_allowed"] is False
    assert payload["fallback_images_allowed"] is False
    assert payload["fake_artifacts_allowed"] is False
    assert payload["inline_image_payloads_allowed"] is False
    assert payload["source_image_selection_implemented"] is False
    assert payload["image_mapping_implemented"] is False
    assert payload["production_pptx_output_implemented"] is False
    assert payload["renderer_runtime_implemented"] is False
    assert "no_production_renderer_closure" in payload["non_goals"]


def test_kr7h12_blocks_missing_source_image_quality_flags() -> None:
    payload = deepcopy(_source_backed_presentation_ir())
    payload["quality_contract"].pop("source_images_only", None)
    payload["quality_contract"].pop("no_generated_images", None)

    validation = validate_renderer_worker_input_payload(payload)

    assert validation.status == "blocked"
    codes = {issue.code for issue in validation.issues}
    assert "source_images_only_not_enforced" in codes
    assert "no_generated_images_not_enforced" in codes


def test_kr7h12_blocks_generated_or_fake_image_assets() -> None:
    payload = deepcopy(_source_backed_presentation_ir())
    payload["assets"] = [
        {
            "asset_id": "generated_image_001",
            "type": "image",
            "mime_type": "image/png",
            "source_type": "generated",
            "generated": True,
            "checksum_sha256": "sha256:fake",
        }
    ]

    validation = validate_renderer_worker_input_payload(payload)

    assert validation.status == "blocked"
    codes = {issue.code for issue in validation.issues}
    assert "non_source_asset_forbidden" in codes
    assert "fake_or_generated_asset_forbidden" in codes


def test_kr7h12_blocks_required_image_without_source_binding() -> None:
    payload = deepcopy(_source_backed_presentation_ir())
    payload["slides"][0]["visual_plan"]["requires_image"] = True

    validation = validate_renderer_worker_input_payload(payload)

    assert validation.status == "blocked"
    assert "source_image_required_but_unbound" in {issue.code for issue in validation.issues}


def test_kr7h12_blocks_inline_or_placeholder_image_blocks() -> None:
    payload = deepcopy(_source_backed_presentation_ir())
    payload["slides"][0]["blocks"] = [
        {
            "block_id": "inline_image",
            "type": "image",
            "semantic_role": "source_image",
            "content": {"data_uri": "data:image/png;base64,ZmFrZQ=="},
            "source_refs": [],
            "data_binding": None,
        }
    ]

    validation = validate_renderer_worker_input_payload(payload)

    assert validation.status == "blocked"
    codes = {issue.code for issue in validation.issues}
    assert "source_image_block_ref_missing" in codes
    assert "fake_or_inline_image_block_forbidden" in codes


def test_kr7h12_accepts_source_backed_image_asset_without_mapping_claim() -> None:
    payload = deepcopy(_source_backed_presentation_ir())
    asset_id = "source_image_asset_001"
    payload["assets"] = [
        {
            "asset_id": asset_id,
            "type": "image",
            "mime_type": "image/png",
            "source_type": "source_asset",
            "source_asset_id": asset_id,
            "source_id": "src_renderer_kr7h12",
            "checksum_sha256": "sha256:" + "1" * 64,
        }
    ]
    slide = payload["slides"][0]
    slide["visual_plan"]["requires_image"] = True
    slide["visual_plan"]["source_image_refs"] = [asset_id]
    slide["blocks"] = [
        {
            "block_id": "source_image_block",
            "type": "image",
            "semantic_role": "source_image",
            "content": {"source_asset_id": asset_id},
            "source_refs": [asset_id],
            "data_binding": {"source_asset_id": asset_id, "source_ref": "src_renderer_kr7h12"},
        }
    ]

    validation = validate_renderer_worker_input_payload(payload)

    assert validation.status == "ready"
    assert validation.renderer_runtime_implemented is False
    assert validation.production_pptx_output_implemented is False
