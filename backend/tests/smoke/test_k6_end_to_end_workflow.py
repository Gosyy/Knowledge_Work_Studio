from __future__ import annotations

from backend.app.services.k_phase.end_to_end_workflow import (
    K6EndToEndWorkflowRequest,
    build_k6_capabilities_report,
    run_k6_end_to_end_workflow,
    validate_k6_end_to_end_result,
)


def _source_text() -> str:
    return (
        "Offline executive reporting requires source-grounded presentations. "
        "Local GigaChat planning creates an editable outline before rendering. "
        "Operators approve the plan before generation. "
        "Renderer quality bounds dense content and selects local templates. "
        "Visual QA inspects local PPTX OOXML for layout risk. "
        "Source-to-slide provenance links every slide to bounded evidence. "
        "The final workflow must remain offline and avoid cloud fallback."
    )


def test_k6_runs_source_to_pptx_operator_gated_workflow() -> None:
    result = run_k6_end_to_end_workflow(
        K6EndToEndWorkflowRequest(
            source_text=_source_text(),
            source_refs=(
                {
                    "kind": "document",
                    "source_id": "memo_001",
                    "title": "K6 operator memo",
                    "locator": "memo.md#workflow",
                    "source_file_id": "file_memo_001",
                    "derived_content_id": "derived_text_001",
                },
            ),
            target_slide_count=7,
            artifact_filename="k6-end-to-end-smoke.pptx",
        )
    )

    assert validate_k6_end_to_end_result(result) == []
    assert result.safe_metadata["checkpoint"] == "K6"
    assert result.safe_metadata["status"] == "ready_for_operator_delivery"
    assert result.safe_metadata["end_to_end_kimi_like_workflow_supported"] is True
    assert result.planning_result.safe_metadata["checkpoint"] == "K1"
    assert result.plan_editor_result.safe_metadata["checkpoint"] == "K2"
    assert result.renderer_quality_result.safe_metadata["checkpoint"] == "K3"
    assert result.visual_qa_result.safe_metadata["checkpoint"] == "K4"
    assert result.provenance_result.safe_metadata["checkpoint"] == "K5"
    assert result.provenance_result.coverage.coverage_status == "complete"
    assert result.visual_qa_result.status in {"passed", "needs_operator_review"}
    assert result.operator_review.decision == "approve"
    assert result.render_result.size_bytes > 0
    assert all(gate.status == "passed" for gate in result.gates)
    assert all(slide.citations for slide in result.provenance_result.plan.slides)
    assert result.manifest["k6_workflow"]["checkpoint"] == "K6"
    assert "source_to_slide_provenance" in result.manifest
    assert result.safe_metadata["network_required"] is False
    assert result.safe_metadata["kimi_level_claimed_by_k6"] is False
    assert result.safe_metadata["whole_project_kimi_level_supported"] is False


def test_k6_capabilities_remain_controlled_scope() -> None:
    capabilities = build_k6_capabilities_report()
    assert capabilities["k1_planning_integrated"] is True
    assert capabilities["k2_plan_editor_approval_integrated"] is True
    assert capabilities["k3_renderer_quality_integrated"] is True
    assert capabilities["k4_visual_qa_integrated"] is True
    assert capabilities["k5_source_to_slide_provenance_integrated"] is True
    assert capabilities["api_endpoint_added_by_k6"] is False
    assert capabilities["db_schema_migration_added_by_k6"] is False
    assert capabilities["frontend_runtime_changed_by_k6"] is False
    assert capabilities["dependency_versions_changed_by_k6"] is False
    assert capabilities["dockerfiles_changed_by_k6"] is False
    assert capabilities["cloud_llm_added_by_k6"] is False
    assert capabilities["cloud_vision_added_by_k6"] is False
    assert capabilities["kimi_level_claimed_by_k6"] is False
