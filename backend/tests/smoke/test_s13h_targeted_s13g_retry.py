from backend.app.services.slides_service.targeted_s13g_retry import (
    KNOWN_FAILED_S13G_SCENARIOS,
    targeted_s13g_retry_report,
)


def test_s13h_contract_ready() -> None:
    report = targeted_s13g_retry_report()
    assert report["status"] == "ready"
    assert report["targeted_retry_failed_s13g_scenarios_ready_by_s13h"] is True
    assert report["scenario_count"] == 12
    assert report["retry_scenario_count"] == 2
    assert set(report["retry_scenario_ids"]) == set(KNOWN_FAILED_S13G_SCENARIOS)
    assert report["reused_canonical_scenario_count"] == 10


def test_s13h_safety_boundaries() -> None:
    report = targeted_s13g_retry_report()
    assert report["completed_human_review_results_present_by_s13h"] is False
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s13h"] is False
    assert report["server3_local_intranet_route_verified_by_s13h"] is False
    assert report["kimi_level_claimed_by_s13h"] is False
    assert report["credential_values_recorded_by_s13h"] is False


def test_s13h_reuses_and_retries_only_expected_scenarios() -> None:
    report = targeted_s13g_retry_report()
    assert "executive_memo_to_board_deck" in report["retry_scenario_ids"]
    assert "browser_evidence_packet_to_cited_deck" in report["retry_scenario_ids"]
    assert "architecture_doc_to_architecture_review" in report["reused_scenario_ids"]


def test_s13h_forbidden_actions_registered() -> None:
    report = targeted_s13g_retry_report()
    forbidden = set(report["forbidden_actions"])
    assert "retry_all_scenarios_when_only_targeted_failures_exist" in forbidden
    assert "discard_canonical_valid_s13g_outputs" in forbidden
    assert "claim_selected_offline_workflow_parity" in forbidden
