from backend.app.services.slides_service.selected_benchmark_execution_packet import (
    ALLOWED_REVIEW_DECISIONS,
    INITIAL_REVIEW_STATE,
    REQUIRED_EVIDENCE_MANIFEST_FIELDS,
    REQUIRED_WORKSHEET_FIELDS,
    selected_benchmark_execution_packet_report,
)


def test_s12_selected_benchmark_execution_packet_ready() -> None:
    report = selected_benchmark_execution_packet_report()
    assert report["status"] == "ready", report["errors"]
    assert report["selected_benchmark_execution_packet_completed_by_s12"] is True
    assert report["scenario_packet_count"] == 12
    assert report["worksheet_count_required_by_s12"] == 12
    assert report["initial_review_state_by_s12"] == INITIAL_REVIEW_STATE


def test_s12_requires_real_human_review_before_selected_parity_claim() -> None:
    report = selected_benchmark_execution_packet_report()
    assert report["completed_human_review_required_before_selected_parity_claim_by_s12"] is True
    assert report["completed_human_review_results_present_by_s12"] is False
    assert report["human_review_results_fabricated_by_s12"] is False
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s12"] is False
    assert report["selected_offline_workflow_parity_claim_requires_future_completed_results_by_s12"] is True
    assert report["auto_approval_allowed_by_s12"] is False


def test_s12_packet_schema_covers_worksheets_and_evidence_manifest() -> None:
    report = selected_benchmark_execution_packet_report()
    packet = report["contract"]["scenario_packets"][0]
    for field in REQUIRED_WORKSHEET_FIELDS:
        assert field in packet["required_worksheet_fields"]
    for field in REQUIRED_EVIDENCE_MANIFEST_FIELDS:
        assert field in packet["required_evidence_manifest_fields"]
    assert set(ALLOWED_REVIEW_DECISIONS) == {"approve", "request_rework", "reject"}


def test_s12_boundaries_and_non_claims() -> None:
    report = selected_benchmark_execution_packet_report()
    assert report["accepted_future_claim_wording_by_s12"] == "Kimi Slides-class offline workflow parity for selected benchmark scenarios."
    assert report["generic_kimi_level_achieved_claim_allowed_by_s12"] is False
    assert report["kimi_level_claimed_by_s12"] is False
    assert report["whole_project_kimi_level_supported"] is False
    assert report["server3_local_intranet_route_verified_by_s12"] is False
    assert report["hidden_public_internet_allowed_by_s12"] is False
    assert report["cloud_research_allowed_by_s12"] is False
    assert report["cloud_vision_allowed_by_s12"] is False
    assert report["api_endpoint_added_by_s12"] is False
    assert report["db_schema_migration_added_by_s12"] is False
    assert report["dependency_versions_changed_by_s12"] is False
