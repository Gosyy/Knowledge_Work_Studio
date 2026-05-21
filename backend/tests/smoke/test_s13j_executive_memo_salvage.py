from backend.app.services.slides_service.canonical_schema_adapter import validate_canonical_s13g_payload
from backend.app.services.slides_service.executive_memo_salvage import (
    S13J_EXPECTED_FINAL_CANONICAL_VALID_COUNT,
    adapt_salvaged_payload_to_canonical,
    executive_memo_salvage_report,
    json_digest,
    salvage_jsonish_minimal_payload,
    text_digest,
)
from backend.app.services.slides_service.single_scenario_s13h_retry import S13I_RETRY_SCENARIO_ID


def test_s13j_executive_memo_salvage_contract_ready() -> None:
    report = executive_memo_salvage_report()
    assert report["status"] == "ready"
    assert report["executive_memo_salvage_ready_by_s13j"] is True
    assert report["scenario_count"] == 12
    assert report["salvage_scenario_ids"] == ["executive_memo_to_board_deck"]
    assert report["reused_canonical_scenario_count"] == 11
    assert report["expected_final_canonical_valid_count_by_s13j"] == S13J_EXPECTED_FINAL_CANONICAL_VALID_COUNT
    assert report["deterministic_salvage_only_by_s13j"] is True
    assert report["calls_gigachat_by_s13j_static_check"] is False


def test_s13j_claim_boundaries() -> None:
    report = executive_memo_salvage_report()
    assert report["completed_human_review_results_present_by_s13j"] is False
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s13j"] is False
    assert report["server3_local_intranet_route_verified_by_s13j"] is False
    assert report["kimi_level_claimed_by_s13j"] is False
    assert report["credential_values_recorded_by_s13j"] is False


def test_s13j_safe_comma_salvage_to_canonical_payload() -> None:
    malformed = '{"scenario_id":"executive_memo_to_board_deck" "deck_title":"Board memo" "storyline":["context","analysis","decision","actions"],"slides":[{"title":"One","purpose":"Purpose","key_claims":["claim"],"visual_intent":"text_box","citation_needs":["source"]}]}'
    result = salvage_jsonish_minimal_payload(malformed, S13I_RETRY_SCENARIO_ID, allow_text_adapter=False)
    assert result.payload is not None
    assert result.used_text_to_minimal_model_adapter is False
    assert "safe_comma_insertion_between_adjacent_fields" in result.actions
    canonical = adapt_salvaged_payload_to_canonical(
        result.payload,
        S13I_RETRY_SCENARIO_ID,
        source_response_digest=json_digest({"choices": []}),
        raw_response_text_digest=text_digest(malformed),
        salvage_result=result,
    )
    assert validate_canonical_s13g_payload(canonical, S13I_RETRY_SCENARIO_ID) == []
    provenance = canonical["adapter_provenance"]
    assert provenance["salvage_generated_fields_are_not_model_generated"] is True
    assert provenance["source_s13i_response_digest"].startswith("sha256:")


def test_s13j_text_adapter_fallback_marks_fields_not_model_generated() -> None:
    malformed = "This is not JSON. It is a board memo outline with no parseable object."
    result = salvage_jsonish_minimal_payload(malformed, S13I_RETRY_SCENARIO_ID)
    assert result.used_text_to_minimal_model_adapter is True
    canonical = adapt_salvaged_payload_to_canonical(
        result.payload,
        S13I_RETRY_SCENARIO_ID,
        source_response_digest=json_digest({"choices": []}),
        raw_response_text_digest=text_digest(malformed),
        salvage_result=result,
    )
    assert validate_canonical_s13g_payload(canonical, S13I_RETRY_SCENARIO_ID) == []
    provenance = canonical["adapter_provenance"]
    assert provenance["model_provided_fields"] == []
    assert provenance["salvage_generated_fields_are_not_model_generated"] is True
    assert "fallback_text_to_minimal_model_adapter" in provenance["normalization_actions"]
