from __future__ import annotations

from backend.app.services.slides_service import (
    RENDERER_WORKER_KR7H_CLOSURE_GATE_SCHEMA_VERSION,
    renderer_worker_kr7h_closure_gate_payload,
)


def test_kr7h13_closure_gate_closes_kr7h_foundation_only() -> None:
    payload = renderer_worker_kr7h_closure_gate_payload()

    assert payload["schema_version"] == RENDERER_WORKER_KR7H_CLOSURE_GATE_SCHEMA_VERSION
    assert payload["status"] == "ready"
    assert payload["kr7h_closure_gate_implemented"] is True
    assert payload["kr7h_phase_closed"] is True
    assert payload["closed_through_phase"] == "KR-7H.13"
    assert payload["completed_layer_count"] == 12
    assert [layer["phase"] for layer in payload["completed_layers"]] == [
        "KR-7H.1",
        "KR-7H.2",
        "KR-7H.3",
        "KR-7H.4",
        "KR-7H.5",
        "KR-7H.6",
        "KR-7H.7",
        "KR-7H.8",
        "KR-7H.9",
        "KR-7H.10",
        "KR-7H.11",
        "KR-7H.12",
    ]
    assert payload["required_checker"] == "scripts/kw_renderer_worker_kr7h_closure_gate_check.py"
    assert payload["required_full_runner_step"] == "29h13-renderer-worker-kr7h-closure-gate-check"


def test_kr7h13_closure_gate_does_not_claim_production_or_quality_closure() -> None:
    payload = renderer_worker_kr7h_closure_gate_payload()

    assert payload["renderer_runtime_implemented"] is False
    assert payload["production_pptx_output_implemented"] is False
    assert payload["production_renderer_closure_implemented"] is False
    assert payload["visual_qa_executed"] is False
    assert payload["visual_quality_score"] is None
    assert payload["source_image_selection_implemented"] is False
    assert payload["image_mapping_implemented"] is False
    assert payload["chart_mapping_implemented"] is False
    assert payload["table_mapping_implemented"] is False
    assert payload["theme_mapping_implemented"] is False
    assert payload["professional_layout_engine_implemented"] is False
    assert payload["kimi_level_quality_claimed"] is False
    assert payload["fake_artifacts_allowed"] is False
    assert payload["fallback_renderer_allowed"] is False
    assert payload["next_phase"] == "KR-7I template and brand understanding"
    assert "no_production_renderer_closure" in payload["non_goals"]
    assert "no_kimi_level_quality_claim" in payload["non_goals"]
