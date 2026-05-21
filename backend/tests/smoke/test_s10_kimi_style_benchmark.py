from __future__ import annotations

from backend.app.services.slides_service.kimi_style_benchmark import (
    ACCEPTED_FINAL_CLAIM_WORDING,
    REQUIRED_S_PHASE_EVIDENCE,
    S10_SCENARIO_IDS,
    kimi_style_benchmark_report,
    validate_kimi_style_benchmark_registry,
)


def test_s10_registry_is_ready() -> None:
    report = kimi_style_benchmark_report()
    assert report["status"] == "ready", report["errors"]
    assert report["expanded_kimi_style_benchmark_completed_by_s10"] is True
    assert report["scenario_count"] == 12
    assert report["required_scenario_count"] == 12
    assert set(report["scenario_ids"]) == set(S10_SCENARIO_IDS)


def test_s10_requires_full_s_phase_evidence_chain() -> None:
    report = kimi_style_benchmark_report()
    assert report["required_s_phase_evidence_count"] == 9
    assert report["required_s_phase_evidence"] == list(REQUIRED_S_PHASE_EVIDENCE)
    for scenario in report["scenarios"].values():
        assert scenario["required_s_phase_evidence"] == list(REQUIRED_S_PHASE_EVIDENCE)
        assert "render_based_visual_qa_report" in scenario["required_outputs"]
        assert "citation_manifest" in scenario["required_outputs"]
        assert len(scenario["acceptance_focus"]) >= 5


def test_s10_human_review_acceptance_policy_is_conservative() -> None:
    report = kimi_style_benchmark_report()
    assert report["completed_human_review_required_by_s10"] is True
    assert report["minimum_approved_scenario_count_for_selected_parity"] == 10
    assert report["rejects_allowed_for_selected_parity"] == 0
    assert report["blocker_defects_allowed_for_selected_parity"] == 0
    assert report["request_rework_allowed_for_selected_parity_claim"] == 0
    assert report["citation_coverage_required_by_s10"] == 1.0
    assert report["render_based_visual_qa_required_by_s10"] is True


def test_s10_does_not_claim_generic_kimi_level_or_server3_verification() -> None:
    report = kimi_style_benchmark_report()
    assert validate_kimi_style_benchmark_registry() == []
    assert report["accepted_final_claim_wording_by_s10"] == ACCEPTED_FINAL_CLAIM_WORDING
    assert report["selected_offline_workflow_parity_claim_supported_after_s10_benchmark"] is False
    assert report["selected_offline_workflow_parity_claim_requires_future_completed_results"] is True
    assert report["whole_project_kimi_level_supported"] is False
    assert report["kimi_level_claimed_by_s10"] is False
    assert report["generic_kimi_level_achieved_claim_allowed_by_s10"] is False
    assert report["public_internet_required_by_s10"] is False
    assert report["hidden_public_internet_allowed_by_s10"] is False
    assert report["cloud_research_allowed_by_s10"] is False
    assert report["cloud_vision_allowed_by_s10"] is False
    assert report["server3_local_intranet_route_verified_by_s10"] is False
