from __future__ import annotations

from backend.app.services.slides_service.conversational_edit_loop import (
    CONVERSATIONAL_EDIT_LOOP_CONTRACT,
    SUPPORTED_EDIT_INTENTS,
    conversational_edit_loop_report,
    validate_conversational_edit_loop_contract,
)


def test_s8_conversational_edit_loop_contract_is_ready() -> None:
    report = conversational_edit_loop_report()
    assert report["status"] == "ready"
    assert report["conversational_edit_loop_completed_by_s8"] is True
    assert report["supported_edit_intent_count"] == len(SUPPORTED_EDIT_INTENTS)


def test_s8_requires_saved_plan_operator_approval_and_citation_revalidation() -> None:
    report = conversational_edit_loop_report()
    assert report["requires_saved_plan_snapshot_by_s8"] is True
    assert report["requires_approved_plan_digest_by_s8"] is True
    assert report["requires_explicit_operator_approval_by_s8"] is True
    assert report["plan_patch_preview_required_by_s8"] is True
    assert report["citation_manifest_required_by_s8"] is True
    assert report["citation_revalidation_required_by_s8"] is True
    assert report["generation_from_transient_prompt_allowed_by_s8"] is False
    assert report["direct_pptx_generation_without_plan_allowed_by_s8"] is False


def test_s8_supports_expected_conversational_edit_intents() -> None:
    report = conversational_edit_loop_report()
    intents = set(report["supported_edit_intents"])
    assert "shorten_deck" in intents
    assert "reframe_for_board" in intents
    assert "add_risk_slide" in intents
    assert "replace_table_with_decision_matrix" in intents
    assert "tighten_citations" in intents


def test_s8_preserves_offline_boundaries_and_no_kimi_claims() -> None:
    report = conversational_edit_loop_report()
    assert report["compatible_with_s2_outline_first_by_s8"] is True
    assert report["compatible_with_s7_offline_citations_by_s8"] is True
    assert report["hidden_public_internet_allowed_by_s8"] is False
    assert report["cloud_research_allowed_by_s8"] is False
    assert report["cloud_vision_allowed_by_s8"] is False
    assert report["public_internet_required_by_s8"] is False
    assert report["kimi_level_claimed_by_s8"] is False
    assert report["server3_local_intranet_route_verified_by_s8"] is False
    assert validate_conversational_edit_loop_contract(CONVERSATIONAL_EDIT_LOOP_CONTRACT) == []
