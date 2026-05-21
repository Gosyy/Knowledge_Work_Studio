from __future__ import annotations

import json

from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.live_benchmark_prompt_schema_hardening import (
    MIN_REQUIRED_SLIDES_PER_SCENARIO,
    REQUIRED_RESPONSE_SCHEMA_FIELDS,
    hardened_prompt_for_scenario,
    live_benchmark_prompt_schema_hardening_report,
    validate_hardened_response_payload,
)


def test_s13d_report_ready() -> None:
    report = live_benchmark_prompt_schema_hardening_report()
    assert report["status"] == "ready"
    assert report["live_benchmark_prompt_schema_hardening_ready_by_s13d"] is True
    assert report["hardened_prompt_policy_count"] == 12
    assert report["hardened_live_rerun_performed_by_static_check"] is False
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s13d"] is False
    assert report["kimi_level_claimed_by_s13d"] is False
    assert report["server3_local_intranet_route_verified_by_s13d"] is False


def test_s13d_hardened_prompt_contains_schema_controls() -> None:
    prompt = hardened_prompt_for_scenario(S10_SCENARIO_IDS[0])
    assert "Return a single valid JSON object only" in prompt
    assert "slide_outline" in prompt
    assert "native_visuals" in prompt
    assert "citation_obligations" in prompt
    assert "render_qa_obligations" in prompt
    assert "safety_boundaries" in prompt
    assert "Do not claim Kimi-level" in prompt


def test_s13d_response_payload_validator_accepts_complete_payload() -> None:
    scenario_id = S10_SCENARIO_IDS[0]
    payload = {field: {} for field in REQUIRED_RESPONSE_SCHEMA_FIELDS}
    payload["scenario_id"] = scenario_id
    payload["title"] = "Executive memo to board deck"
    payload["scenario_summary"] = "Specific summary"
    payload["slide_outline"] = [
        {
            "slide_id": f"s{index:02d}",
            "title": f"Slide {index}",
            "purpose": "specific purpose",
            "source_grounding_required": True,
            "native_visuals": ["pptx_table"],
            "citation_requirements": ["claim_to_source_fragment"],
            "render_qa_checks": ["title_body_collision"],
        }
        for index in range(1, MIN_REQUIRED_SLIDES_PER_SCENARIO + 1)
    ]
    payload["safety_boundaries"] = {
        "selected_parity_claim_supported_now": False,
        "kimi_level_claimed": False,
        "server3_local_intranet_verified": False,
        "completed_human_review_results_present": False,
        "credential_values_recorded": False,
    }
    assert validate_hardened_response_payload(payload, scenario_id) == []


def test_s13d_response_payload_validator_rejects_generic_incomplete_payload() -> None:
    errors = validate_hardened_response_payload({"scenario_id": S10_SCENARIO_IDS[0], "slide_outline": []}, S10_SCENARIO_IDS[0])
    assert errors
    assert any("missing response field" in error for error in errors)
    assert any("slide_outline" in error for error in errors)
