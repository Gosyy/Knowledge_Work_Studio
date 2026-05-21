from backend.app.services.slides_service.live_gigachat_selected_benchmark import (
    PUBLIC_API_DEV_ROUTE,
    REQUIRED_PROVIDER,
    S13B_WORKFLOW_ID,
    live_gigachat_selected_benchmark_report,
)


def test_s13b_contract_ready_without_live_credentials() -> None:
    report = live_gigachat_selected_benchmark_report({})
    assert report["status"] == "ready"
    assert report["workflow_id"] == S13B_WORKFLOW_ID
    assert report["scenario_live_generation_spec_count"] == 12
    assert report["provider_required_by_s13b"] == REQUIRED_PROVIDER
    assert report["route_required_by_s13b"] == PUBLIC_API_DEV_ROUTE


def test_s13b_requires_shell_env_but_records_no_secret_values() -> None:
    report = live_gigachat_selected_benchmark_report({"KW_RC3_GIGACHAT_AUTHORIZATION_KEY": "redacted"})
    assert report["requires_shell_env_credentials_by_s13b"] is True
    assert report["credential_inputs_configured_count"] == 1
    assert report["credential_values_recorded_by_s13b"] is False


def test_s13b_does_not_claim_parity_or_server3() -> None:
    report = live_gigachat_selected_benchmark_report({})
    assert report["public_api_dev_execution_performed_by_s13b_static_check"] is False
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s13b"] is False
    assert report["completed_human_review_results_present_by_s13b"] is False
    assert report["server3_local_intranet_route_verified_by_s13b"] is False
    assert report["kimi_level_claimed_by_s13b"] is False
    assert report["whole_project_kimi_level_supported"] is False


def test_s13b_scenario_specs_cover_all_required_controls() -> None:
    report = live_gigachat_selected_benchmark_report({})
    specs = report["contract"]["live_scenario_specs"]
    assert len(specs) == 12
    for spec in specs:
        assert spec["provider"] == "GigaChat"
        assert spec["route"] == "public_api_dev"
        assert spec["public_api_dev_generation_required"] is True
        assert spec["credential_values_recorded"] is False
        assert spec["production_server3_local_intranet_verified"] is False
        assert spec["completed_human_review_results_present"] is False
        assert spec["selected_parity_claim_supported_now"] is False
        assert spec["kimi_level_claimed"] is False
