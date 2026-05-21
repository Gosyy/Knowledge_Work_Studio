from backend.app.services.slides_service.canonical_schema_adapter import (
    CANONICAL_ADAPTER_POLICIES,
    adapt_minimal_model_payload_to_canonical,
    canonical_schema_adapter_report,
    minimal_prompt_for_scenario,
    validate_canonical_s13g_payload,
)
from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.strict_json_per_scenario_rerun import MIN_REQUIRED_SLIDES_PER_SCENARIO


def test_s13g_report_ready_and_safe():
    report = canonical_schema_adapter_report()
    assert report["status"] == "ready"
    assert report["canonical_schema_adapter_ready_by_s13g"] is True
    assert report["scenario_count"] == 12
    assert report["minimal_prompt_required_by_s13g"] is True
    assert report["canonical_adapter_required_by_s13g"] is True
    assert report["adapter_provenance_required_by_s13g"] is True
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s13g"] is False
    assert report["server3_local_intranet_route_verified_by_s13g"] is False
    assert report["kimi_level_claimed_by_s13g"] is False


def test_s13g_policies_cover_all_scenarios():
    assert len(CANONICAL_ADAPTER_POLICIES) == len(S10_SCENARIO_IDS)
    assert {policy.scenario_id for policy in CANONICAL_ADAPTER_POLICIES} == set(S10_SCENARIO_IDS)
    assert all(policy.static_check_calls_gigachat is False for policy in CANONICAL_ADAPTER_POLICIES)


def test_s13g_adapter_normalizes_minimal_model_payload():
    scenario_id = S10_SCENARIO_IDS[0]
    model_payload = {
        "scenario_id": scenario_id,
        "deck_title": "Executive memo deck",
        "storyline": ["context", "analysis", "decision", "actions"],
        "slides": [
            {
                "title": f"Slide {index}",
                "purpose": f"Purpose {index}",
                "key_claims": ["claim"],
                "visual_intent": "pptx_table",
                "citation_needs": ["source"],
            }
            for index in range(1, MIN_REQUIRED_SLIDES_PER_SCENARIO + 1)
        ],
        "risks_or_open_questions": ["source coverage"],
    }
    canonical = adapt_minimal_model_payload_to_canonical(model_payload, scenario_id)
    assert validate_canonical_s13g_payload(canonical, scenario_id) == []
    assert canonical["adapter_provenance"]["adapter_fields_are_not_model_generated"] is True
    assert len(canonical["slide_outline"]) >= MIN_REQUIRED_SLIDES_PER_SCENARIO


def test_s13g_minimal_prompt_contains_boundaries():
    prompt = minimal_prompt_for_scenario(S10_SCENARIO_IDS[0])
    assert "Return exactly one small JSON object" in prompt
    assert "Do not claim Kimi-level" in prompt
    assert "Do not use markdown fences" in prompt
