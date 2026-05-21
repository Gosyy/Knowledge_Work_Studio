from backend.app.services.slides_service.live_gigachat_evidence_packet import (
    LIVE_EVIDENCE_PACKET_SPECS,
    REQUIRED_EVIDENCE_PACKET_COMPONENTS,
    REQUIRED_LIVE_INPUTS,
    live_gigachat_evidence_packet_export_report,
    validate_live_gigachat_evidence_packet_export_contract,
)


def test_s13c_contract_ready() -> None:
    assert validate_live_gigachat_evidence_packet_export_contract() == []
    report = live_gigachat_evidence_packet_export_report()
    assert report["status"] == "ready"
    assert report["live_gigachat_evidence_packet_export_contract_ready_by_s13c"] is True


def test_s13c_has_twelve_scenario_specs() -> None:
    report = live_gigachat_evidence_packet_export_report()
    assert len(LIVE_EVIDENCE_PACKET_SPECS) == 12
    assert report["scenario_evidence_packet_count"] == 12
    assert report["review_state_after_s13c"] == "pending_human_review"


def test_s13c_preserves_claim_safety_boundaries() -> None:
    report = live_gigachat_evidence_packet_export_report()
    assert report["live_generation_performed_by_s13c_static_check"] is False
    assert report["completed_human_review_results_present_by_s13c"] is False
    assert report["human_review_results_fabricated_by_s13c"] is False
    assert report["auto_approval_allowed_by_s13c"] is False
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s13c"] is False
    assert report["server3_local_intranet_route_verified_by_s13c"] is False
    assert report["public_api_dev_route_is_not_server3_proof_by_s13c"] is True
    assert report["kimi_level_claimed_by_s13c"] is False


def test_s13c_required_packet_components_and_inputs() -> None:
    report = live_gigachat_evidence_packet_export_report()
    for item in REQUIRED_LIVE_INPUTS:
        assert item in report["required_live_inputs"]
    for component in REQUIRED_EVIDENCE_PACKET_COMPONENTS:
        assert component in report["required_evidence_packet_components"]
    assert report["response_digest_required_by_s13c"] is True
    assert report["credential_values_recorded_by_s13c"] is False
