from __future__ import annotations

import json

from backend.app.services.slides_service.hardened_output_repair import (
    hardened_output_repair_report,
    repair_hardened_response_text,
)


def _valid_payload(scenario_id: str) -> dict:
    slides = [
        {
            "slide_id": f"s{index:02d}",
            "title": f"Slide {index}",
            "purpose": "scenario-specific purpose",
            "source_grounding_required": True,
            "native_visuals": ["pptx_table"],
            "citation_requirements": ["claim_to_source_fragment_mapping_required"],
            "render_qa_checks": ["title_body_collision", "table_overflow"],
        }
        for index in range(1, 9)
    ]
    return {
        "scenario_id": scenario_id,
        "title": "Scenario deck",
        "scenario_summary": "Scenario-specific summary.",
        "approved_plan_candidate": {
            "storyline": ["context", "analysis", "decision", "next actions"],
            "assumptions_to_verify": ["source evidence exists"],
            "non_goals": ["no approval"],
        },
        "slide_outline": slides,
        "native_visuals": [
            {
                "visual_id": "v01",
                "visual_type": "pptx_table",
                "editable_pptx_native": True,
                "source_fields_required": ["source_id", "fragment_id"],
                "render_qa_checks": ["table_overflow"],
            }
        ],
        "citation_obligations": {"slide_level_claims_require_sources": True},
        "render_qa_obligations": {"actual_slide_render_required": True},
        "evidence_manifest": {"required_outputs": ["generated_pptx"]},
        "human_review_handoff": {"review_state": "pending_human_review", "do_not_auto_fill": True},
        "safety_boundaries": {
            "selected_parity_claim_supported_now": False,
            "kimi_level_claimed": False,
            "server3_local_intranet_verified": False,
            "completed_human_review_results_present": False,
            "credential_values_recorded": False,
        },
    }


def test_s13e_contract_ready() -> None:
    report = hardened_output_repair_report()
    assert report["status"] == "ready"
    assert report["deterministic_repair_only_by_s13e"] is True
    assert report["live_gigachat_call_allowed_by_s13e"] is False
    assert report["completed_human_review_results_present_by_s13e"] is False


def test_s13e_repairs_markdown_fence_and_trailing_data() -> None:
    scenario_id = "executive_memo_to_board_deck"
    text = "```json\n" + json.dumps(_valid_payload(scenario_id), ensure_ascii=False) + "\n```  }"
    result = repair_hardened_response_text(text, scenario_id)
    assert result.schema_valid is True
    assert "strip_markdown_code_fences" in result.repair_actions_applied
    assert "trim_trailing_extra_data" in result.repair_actions_applied


def test_s13e_normalizes_nested_approved_plan_candidate_fields() -> None:
    scenario_id = "executive_memo_to_board_deck"
    payload = {
        "scenario_id": scenario_id,
        "title": "Scenario deck",
        "scenario_summary": "Nested response.",
        "approved_plan_candidate": _valid_payload(scenario_id),
        "safety_boundaries": {
            "selected_parity_claim_supported_now": False,
            "kimi_level_claimed": False,
            "server3_local_intranet_verified": False,
            "completed_human_review_results_present": False,
            "credential_values_recorded": False,
        },
    }
    text = json.dumps(payload, ensure_ascii=False)
    result = repair_hardened_response_text(text, scenario_id)
    assert result.schema_valid is True
    assert "normalize_approved_plan_candidate_nested_schema_fields" in result.repair_actions_applied


def test_s13e_rejects_wrong_scenario_id() -> None:
    text = json.dumps(_valid_payload("executive_memo_to_board_deck"), ensure_ascii=False)
    result = repair_hardened_response_text(text, "architecture_doc_to_architecture_review")
    assert result.schema_valid is False
    assert any("scenario_id mismatch" in error for error in result.schema_errors)
