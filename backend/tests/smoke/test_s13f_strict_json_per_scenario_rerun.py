from __future__ import annotations

from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.strict_json_per_scenario_rerun import (
    MIN_REQUIRED_SLIDES_PER_SCENARIO,
    build_minimal_valid_s13f_payload,
    strict_json_per_scenario_rerun_report,
    strict_json_prompt_for_scenario,
    validate_strict_s13f_payload,
)


def test_s13f_contract_ready() -> None:
    report = strict_json_per_scenario_rerun_report()
    assert report["status"] == "ready", report["errors"]
    assert report["scenario_count"] == 12
    assert report["strict_json_only_by_s13f"] is True
    assert report["schema_echo_required_by_s13f"] is True
    assert report["repair_fallback_allowed_by_s13f"] is True
    assert report["static_check_calls_gigachat_by_s13f"] is False
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s13f"] is False
    assert report["server3_local_intranet_route_verified_by_s13f"] is False
    assert report["kimi_level_claimed_by_s13f"] is False


def test_s13f_minimal_payload_validates() -> None:
    scenario_id = S10_SCENARIO_IDS[0]
    payload = build_minimal_valid_s13f_payload(scenario_id)
    assert len(payload["slide_outline"]) >= MIN_REQUIRED_SLIDES_PER_SCENARIO
    assert validate_strict_s13f_payload(payload, scenario_id) == []


def test_s13f_rejects_missing_purpose() -> None:
    scenario_id = S10_SCENARIO_IDS[0]
    payload = build_minimal_valid_s13f_payload(scenario_id)
    del payload["slide_outline"][0]["purpose"]
    assert any("purpose" in err for err in validate_strict_s13f_payload(payload, scenario_id))


def test_s13f_prompt_contains_strict_boundaries() -> None:
    prompt = strict_json_prompt_for_scenario(S10_SCENARIO_IDS[0])
    assert "Return exactly one JSON object" in prompt
    assert "schema_echo" in prompt
    assert "safety boundaries" in prompt
