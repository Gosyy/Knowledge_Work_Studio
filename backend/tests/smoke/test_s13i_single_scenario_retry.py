from backend.app.services.slides_service.single_scenario_s13h_retry import (
    S13I_RETRY_SCENARIO_ID,
    single_scenario_executive_memo_retry_report,
)


def test_s13i_single_scenario_retry_contract_ready() -> None:
    report = single_scenario_executive_memo_retry_report()
    assert report["status"] == "ready"
    assert report["single_scenario_executive_memo_retry_ready_by_s13i"] is True
    assert report["scenario_count"] == 12
    assert report["retry_scenario_count"] == 1
    assert report["retry_scenario_ids"] == ["executive_memo_to_board_deck"]
    assert report["reused_canonical_scenario_count"] == 11
    assert report["single_scenario_retry_only_by_s13i"] is True


def test_s13i_claim_boundaries() -> None:
    report = single_scenario_executive_memo_retry_report()
    assert report["completed_human_review_results_present_by_s13i"] is False
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s13i"] is False
    assert report["server3_local_intranet_route_verified_by_s13i"] is False
    assert report["kimi_level_claimed_by_s13i"] is False
    assert report["credential_values_recorded_by_s13i"] is False


def test_s13i_retry_scenario_constant() -> None:
    assert S13I_RETRY_SCENARIO_ID == "executive_memo_to_board_deck"
