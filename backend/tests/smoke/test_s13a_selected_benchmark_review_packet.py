
from backend.app.services.slides_service.selected_benchmark_review_packet import (
    selected_benchmark_review_packet_skeleton_report,
)


def test_s13a_selected_benchmark_review_packet_ready() -> None:
    report = selected_benchmark_review_packet_skeleton_report()
    assert report["status"] == "ready"
    assert report["selected_benchmark_review_packet_skeleton_completed_by_s13a"] is True
    assert report["scenario_review_packet_count"] == 12
    assert report["worksheet_count_required_by_s13a"] == 12


def test_s13a_does_not_run_live_or_fabricate_review() -> None:
    report = selected_benchmark_review_packet_skeleton_report()
    assert report["live_gigachat_required_by_s13a"] is False
    assert report["public_api_dev_execution_performed_by_s13a"] is False
    assert report["completed_human_review_results_present_by_s13a"] is False
    assert report["human_review_results_fabricated_by_s13a"] is False
    assert report["auto_approval_allowed_by_s13a"] is False


def test_s13a_keeps_claim_boundaries() -> None:
    report = selected_benchmark_review_packet_skeleton_report()
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s13a"] is False
    assert report["selected_offline_workflow_parity_claim_requires_future_completed_results_by_s13a"] is True
    assert report["kimi_level_claimed_by_s13a"] is False
    assert report["whole_project_kimi_level_supported"] is False
    assert report["server3_local_intranet_route_verified_by_s13a"] is False


def test_s13a_preserves_offline_cloud_boundaries() -> None:
    report = selected_benchmark_review_packet_skeleton_report()
    assert report["hidden_public_internet_allowed_by_s13a"] is False
    assert report["cloud_research_allowed_by_s13a"] is False
    assert report["cloud_vision_allowed_by_s13a"] is False
    assert report["public_internet_required_by_s13a"] is False
    assert report["api_endpoint_added_by_s13a"] is False
    assert report["db_schema_migration_added_by_s13a"] is False
    assert report["dependency_versions_changed_by_s13a"] is False
