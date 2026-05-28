from __future__ import annotations

from copy import deepcopy

from backend.app.services.slides_service import (
    PRESENTATION_IR_SCHEMA_VERSION,
    RENDERER_WORKER_ARTIFACT_BUNDLE_SCHEMA_VERSION,
    RENDERER_WORKER_CONTRACT_SCHEMA_VERSION,
    RENDERER_WORKER_INPUT_SCHEMA_VERSION,
    RENDERER_WORKER_PROOF_BUNDLE_SCHEMA_VERSION,
    RENDERER_WORKER_RUNTIME_IMPLEMENTED,
    OfflineEvidenceIndexBuilder,
    OfflineSourceIngestionEngine,
    PresentationIRPlannerFoundation,
    PresentationIRPlannerRequest,
    build_renderer_worker_input_payload,
    renderer_worker_boundary_contract_payload,
    validate_renderer_worker_input_payload,
)


def _source_backed_presentation_ir() -> dict[str, object]:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Retention\n\nCustomer retention improved after support automation.\n\n# Risk\n\nDeployment risk decreased after rollout automation.",
        source_id="src_renderer",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h1",
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


def test_kr7h1_renderer_worker_boundary_contract_is_contract_only() -> None:
    contract = renderer_worker_boundary_contract_payload()

    assert contract["schema_version"] == RENDERER_WORKER_CONTRACT_SCHEMA_VERSION
    assert contract["renderer_runtime_implemented"] is False
    assert contract["production_pptx_output_implemented"] is False
    assert contract["proof_bundle_runtime_implemented"] is False
    assert contract["input_schema_version"] == RENDERER_WORKER_INPUT_SCHEMA_VERSION
    assert contract["artifact_bundle_schema_version"] == RENDERER_WORKER_ARTIFACT_BUNDLE_SCHEMA_VERSION
    assert contract["proof_bundle_schema_version"] == RENDERER_WORKER_PROOF_BUNDLE_SCHEMA_VERSION
    assert contract["boundary_chain"] == [
        "python_backend_builds_presentation_ir",
        "node_pptxgenjs_worker_receives_json",
        "pptxgenjs_creates_native_editable_pptx",
        "libreoffice_renders_pdf_png_proof",
        "backend_stores_artifact_and_proof_bundle",
    ]
    assert "no_production_quality_output_claims" in contract["non_goals"]


def test_kr7h1_renderer_worker_input_contract_accepts_source_backed_presentation_ir() -> None:
    payload = _source_backed_presentation_ir()
    validation = validate_renderer_worker_input_payload(payload)
    worker_input = build_renderer_worker_input_payload(payload, request_id="req_contract")

    assert validation.status == "ready"
    assert validation.renderer_runtime_implemented is RENDERER_WORKER_RUNTIME_IMPLEMENTED
    assert worker_input["schema_version"] == RENDERER_WORKER_INPUT_SCHEMA_VERSION
    assert worker_input["renderer_runtime_implemented"] is False
    assert worker_input["artifact_bundle_produced"] is False
    assert worker_input["proof_bundle_produced"] is False
    assert worker_input["status"] == "ready"
    assert worker_input["presentation_ir_schema_version"] == PRESENTATION_IR_SCHEMA_VERSION
    assert worker_input["presentation_ir"]["schema_version"] == PRESENTATION_IR_SCHEMA_VERSION


def test_kr7h1_renderer_worker_input_blocks_prompt_only_visual_grammar_gaps() -> None:
    result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_prompt_only_renderer",
            title="Draft without sources",
            objective="Do not render source-backed visuals without evidence",
            require_evidence=False,
            slide_count=3,
        ),
        OfflineEvidenceIndexBuilder().build_index([]),
    )
    assert result.presentation_ir is not None

    validation = validate_renderer_worker_input_payload(result.presentation_ir)

    assert validation.status == "blocked"
    assert "visual_grammar_binding_blocked" in {issue.code for issue in validation.issues}
    assert validation.renderer_runtime_implemented is False


def test_kr7h1_renderer_worker_input_blocks_fake_native_chart_data() -> None:
    payload = deepcopy(_source_backed_presentation_ir())
    slide = payload["slides"][1]
    slide["blocks"] = [
        {
            "block_id": "fake_chart",
            "type": "native_chart",
            "semantic_role": "evidence_chart",
            "content": {"chart_type": "bar", "series": [{"name": "Fake", "values": ["invented"]}]},
            "source_refs": ["src_renderer#fragment"],
            "data_binding": {"source_ref": "src_renderer"},
        }
    ]

    validation = validate_renderer_worker_input_payload(payload)

    assert validation.status == "blocked"
    assert "visual_grammar_missing_data_binding_key" in {issue.code for issue in validation.issues}
    assert "visual_grammar_native_chart_requires_real_numeric_data" in {issue.code for issue in validation.issues}


def test_kr7h1_renderer_worker_input_rejects_runtime_output_claims() -> None:
    payload = deepcopy(_source_backed_presentation_ir())
    payload["quality_contract"]["renderer_runtime_implemented"] = True
    payload["quality_contract"]["production_pptx_output_implemented"] = True

    validation = validate_renderer_worker_input_payload(payload)

    assert validation.status == "blocked"
    codes = {issue.code for issue in validation.issues}
    assert "unsupported_renderer_runtime_claim" in codes
    assert "unsupported_production_output_claim" in codes
