from __future__ import annotations

from copy import deepcopy

import pytest

from backend.app.services.slides_service import (
    RENDERER_WORKER_DRY_RUN_IMPLEMENTED,
    RENDERER_WORKER_DRY_RUN_SCHEMA_VERSION,
    RENDERER_WORKER_INPUT_SCHEMA_VERSION,
    RENDERER_WORKER_INVOCATION_MANIFEST_SCHEMA_VERSION,
    OfflineEvidenceIndexBuilder,
    OfflineSourceIngestionEngine,
    PresentationIRPlannerFoundation,
    PresentationIRPlannerRequest,
    build_renderer_worker_dry_run_report,
    renderer_worker_dry_run_capabilities,
    require_renderer_worker_dry_run_ready,
)


def _source_backed_presentation_ir() -> dict[str, object]:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Retention\n\nCustomer retention improved after support automation.\n\n# Risk\n\nDeployment risk decreased after rollout automation.",
        source_id="src_renderer_dry_run",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h2",
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


def test_kr7h2_dry_run_capabilities_are_contract_only() -> None:
    capabilities = renderer_worker_dry_run_capabilities()

    assert capabilities["schema_version"] == RENDERER_WORKER_DRY_RUN_SCHEMA_VERSION
    assert capabilities["dry_run_implemented"] is RENDERER_WORKER_DRY_RUN_IMPLEMENTED
    assert capabilities["renderer_runtime_implemented"] is False
    assert capabilities["production_pptx_output_implemented"] is False
    assert capabilities["artifact_bundle_produced"] is False
    assert capabilities["proof_bundle_produced"] is False
    assert "emit_invocation_manifest_without_runtime_execution" in capabilities["dry_run_chain"]
    assert "start_node_worker" in capabilities["blocked_runtime_actions"]
    assert "no_pptxgenjs_dependency_addition" in capabilities["non_goals"]


def test_kr7h2_dry_run_accepts_source_backed_presentation_ir_without_runtime_output() -> None:
    result = build_renderer_worker_dry_run_report(_source_backed_presentation_ir(), request_id="req_dry_run")

    assert result.status == "ready"
    assert result.schema_version == RENDERER_WORKER_DRY_RUN_SCHEMA_VERSION
    assert result.renderer_runtime_implemented is False
    assert result.dry_run_implemented is True
    assert result.artifact_bundle_produced is False
    assert result.proof_bundle_produced is False
    assert result.renderer_input is not None
    assert result.renderer_input["schema_version"] == RENDERER_WORKER_INPUT_SCHEMA_VERSION
    assert result.renderer_input["renderer_runtime_implemented"] is False
    assert result.invocation_manifest is not None
    assert result.invocation_manifest["schema_version"] == RENDERER_WORKER_INVOCATION_MANIFEST_SCHEMA_VERSION
    assert result.invocation_manifest["status"] == "dry_run_ready"
    assert result.invocation_manifest["would_invoke"]["runtime"] == "node_pptxgenjs_worker"
    assert "start_node_worker" in result.invocation_manifest["blocked_runtime_actions"]
    assert result.invocation_manifest["artifact_bundle_produced"] is False
    assert result.invocation_manifest["proof_bundle_produced"] is False


def test_kr7h2_dry_run_blocks_prompt_only_visual_grammar_gaps() -> None:
    planner_result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_dry_run_prompt_only",
            title="Draft without sources",
            objective="Do not render source-backed visuals without evidence",
            require_evidence=False,
            slide_count=3,
        ),
        OfflineEvidenceIndexBuilder().build_index([]),
    )
    assert planner_result.presentation_ir is not None

    dry_run = build_renderer_worker_dry_run_report(planner_result.presentation_ir)

    assert dry_run.status == "blocked"
    assert dry_run.renderer_input is None
    assert dry_run.invocation_manifest is None
    assert "visual_grammar_binding_blocked" in {issue.code for issue in dry_run.issues}


def test_kr7h2_dry_run_blocks_fake_native_chart_data() -> None:
    payload = deepcopy(_source_backed_presentation_ir())
    slide = payload["slides"][1]
    slide["blocks"] = [
        {
            "block_id": "fake_chart",
            "type": "native_chart",
            "semantic_role": "evidence_chart",
            "content": {"chart_type": "bar", "series": [{"name": "Fake", "values": ["invented"]}]},
            "source_refs": ["src_renderer_dry_run#fragment"],
            "data_binding": {"source_ref": "src_renderer_dry_run"},
        }
    ]

    dry_run = build_renderer_worker_dry_run_report(payload)

    assert dry_run.status == "blocked"
    codes = {issue.code for issue in dry_run.issues}
    assert "visual_grammar_missing_data_binding_key" in codes
    assert "visual_grammar_native_chart_requires_real_numeric_data" in codes


def test_kr7h2_require_dry_run_ready_fails_closed() -> None:
    planner_result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_dry_run_blocked",
            title="Draft without sources",
            objective="Do not render without evidence",
            require_evidence=False,
            slide_count=3,
        ),
        OfflineEvidenceIndexBuilder().build_index([]),
    )
    assert planner_result.presentation_ir is not None
    dry_run = build_renderer_worker_dry_run_report(planner_result.presentation_ir)

    with pytest.raises(ValueError, match="Renderer worker dry run is blocked"):
        require_renderer_worker_dry_run_ready(dry_run)
