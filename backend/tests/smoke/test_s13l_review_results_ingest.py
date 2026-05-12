from __future__ import annotations

import json
import zipfile
from pathlib import Path

from backend.app.services.slides_service.kimi_style_benchmark import REQUIRED_HUMAN_REVIEW_DIMENSIONS, S10_SCENARIO_IDS
from backend.app.services.slides_service.s13j_human_review_packet import S13K_SALVAGE_SCENARIO_ID
from backend.app.services.slides_service.s13k_review_results_ingest import (
    build_s13l_ingest_report,
    s13l_review_results_ingest_report,
    zip_ingest_artifacts,
)


def _scores(value: int = 2) -> dict[str, int]:
    return {dimension: value for dimension in REQUIRED_HUMAN_REVIEW_DIMENSIONS}


def _packet_index() -> dict:
    return {
        "schema_version": "s13k.human_review_packet_from_s13j.v1",
        "s_phase": "S13k-export",
        "status": "ready",
        "scenario_count": 12,
        "review_state": "pending_human_review",
        "completed_human_review_results_present": False,
        "auto_approval_allowed": False,
        "selected_offline_workflow_parity_claim_supported_now": False,
        "kimi_level_claimed": False,
        "server3_local_intranet_route_verified": False,
        "credential_values_recorded": False,
        "raw_secret_values_recorded": False,
        "fallback_text_to_minimal_model_adapter_marker_preserved": True,
        "scenario_packets": [
            {
                "scenario_id": scenario_id,
                "worksheet_id": f"s13k_worksheet_{index:02d}_{scenario_id}",
                "canonical_payload_digest": f"sha256:{index:064d}",
                "review_state": "pending_human_review",
                "auto_approval_allowed": False,
                "selected_offline_workflow_parity_claim_supported_now": False,
                "kimi_level_claimed": False,
                "server3_local_intranet_route_verified": False,
                "salvage_provenance_required": scenario_id == S13K_SALVAGE_SCENARIO_ID,
                "used_text_to_minimal_model_adapter": scenario_id == S13K_SALVAGE_SCENARIO_ID,
            }
            for index, scenario_id in enumerate(S10_SCENARIO_IDS, start=1)
        ],
    }


def _worksheet(index: int, scenario_id: str, *, decision: str = "request_rework") -> dict:
    is_salvage = scenario_id == S13K_SALVAGE_SCENARIO_ID
    return {
        "schema_version": "s13k.human_review_packet_from_s13j.v1",
        "worksheet_id": f"s13k_worksheet_{index:02d}_{scenario_id}",
        "scenario_id": scenario_id,
        "review_state": "completed_review",
        "reviewer_id": "assistant-assisted-reviewer",
        "reviewer_type": "assistant_assisted_manual_review_not_independent_human_signature",
        "reviewed_at": "2026-05-12T12:25:00+02:00",
        "decision": decision,
        "allowed_decisions": ["approve", "request_rework", "reject"],
        "required_human_review_dimensions": list(REQUIRED_HUMAN_REVIEW_DIMENSIONS),
        "scores": _scores(2 if decision != "approve" else 4),
        "slide_level_findings": [{"severity": "major", "finding": "generic output needs rework"}],
        "visual_defects": [{"severity": "blocker", "defect_type": "generated_pptx_missing", "finding": "PPTX missing"}]
        if decision != "approve"
        else [],
        "citation_findings": [{"severity": "blocker", "finding": "citations missing"}] if decision != "approve" else [],
        "follow_up_backlog": [{"priority": "P0", "area": "evidence_pack", "summary": "Generate real evidence."}]
        if decision != "approve"
        else [],
        "claim_safety_acknowledgement": True,
        "salvage_provenance_acknowledgement": True,
        "salvage_provenance_required": is_salvage,
        "salvage_method": "fallback_text_to_minimal_model_adapter" if is_salvage else None,
        "used_text_to_minimal_model_adapter": is_salvage,
        "salvage_generated_fields_are_not_model_generated": is_salvage,
        "source_s13i_response_digest": "sha256:source-response" if is_salvage else None,
        "canonical_payload_digest": f"sha256:{index:064d}",
        "completed_human_review_results_present": True,
        "human_review_results_fabricated": False,
        "auto_approval_allowed": False,
        "selected_offline_workflow_parity_claim_supported_now": False,
        "kimi_level_claimed": False,
        "server3_local_intranet_route_verified": False,
        "decision_reason": "request rework because evidence is missing" if decision != "approve" else "approved by reviewer",
    }


def _write_packet_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("packet_index.json", json.dumps(_packet_index()))


def _write_review_results_zip(path: Path, *, mutate_first: dict | None = None, all_approve: bool = False) -> None:
    worksheets = []
    counts = {"approve": 0, "request_rework": 0, "reject": 0}
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for index, scenario_id in enumerate(S10_SCENARIO_IDS, start=1):
            worksheet = _worksheet(index, scenario_id, decision="approve" if all_approve else "request_rework")
            if index == 1 and mutate_first:
                worksheet.update(mutate_first)
            counts[str(worksheet.get("decision") or "")] = counts.get(str(worksheet.get("decision") or ""), 0) + 1
            worksheets.append(
                {
                    "worksheet_file": f"completed_worksheets/{index:02d}_{scenario_id}_worksheet.json",
                    "worksheet_id": worksheet["worksheet_id"],
                    "scenario_id": scenario_id,
                    "decision": worksheet["decision"],
                    "scores": worksheet["scores"],
                    "decision_reason": worksheet.get("decision_reason"),
                }
            )
            zf.writestr(f"completed_worksheets/{index:02d}_{scenario_id}_worksheet.json", json.dumps(worksheet))
        manifest = {
            "schema_version": "s13k.assistant_assisted_manual_review_results.v1",
            "source_packet": "s13k-human-review-packet.zip",
            "reviewed_at": "2026-05-12T12:25:00+02:00",
            "reviewer_id": "assistant-assisted-reviewer",
            "reviewer_type": "assistant_assisted_manual_review_not_independent_human_signature",
            "review_basis": ["S13k packet contents only"],
            "not_reviewed_because_absent_from_packet": ["generated PPTX files"],
            "decision_counts": {key: counts.get(key, 0) for key in ("approve", "request_rework", "reject")},
            "selected_offline_workflow_parity_claim_supported": False,
            "kimi_level_claimed": False,
            "server3_local_intranet_route_verified": False,
            "human_reviewer_signature_required_for_strict_human_review": True,
            "worksheets": worksheets,
        }
        zf.writestr("s13k_manual_review_results.json", json.dumps(manifest))
        zf.writestr("s13k_manual_review_summary.md", "# summary\n")


def test_s13l_static_contract_ready() -> None:
    report = s13l_review_results_ingest_report()
    assert report["status"] == "ready"
    assert report["requires_completed_s13k_review_results_by_s13l"] is True
    assert report["calls_gigachat_by_s13l"] is False
    assert report["auto_approval_allowed_by_s13l"] is False
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s13l"] is False
    assert report["server3_local_intranet_route_verified_by_s13l"] is False


def test_s13l_ingests_completed_request_rework_results(tmp_path: Path) -> None:
    packet_zip = tmp_path / "s13k-packet.zip"
    review_zip = tmp_path / "review-results.zip"
    artifacts_dir = tmp_path / "artifacts"
    out_zip = tmp_path / "s13l.zip"
    _write_packet_zip(packet_zip)
    _write_review_results_zip(review_zip)

    report = build_s13l_ingest_report(review_zip, s13k_packet_input=packet_zip, artifacts_dir=artifacts_dir)
    zip_ingest_artifacts(artifacts_dir, out_zip)

    assert report["status"] == "ready"
    assert report["completed_human_review_decision_count"] == 12
    assert report["approve_count"] == 0
    assert report["request_rework_count"] == 12
    assert report["release_decision_after_s13l"] == "request_rework"
    assert report["selected_offline_workflow_parity_claim_supported_after_s13l"] is False
    assert report["strict_human_signature_required_for_strict_human_review"] is True
    assert (artifacts_dir / "s13l_completed_review_results_ingest_manifest.json").exists()
    assert (artifacts_dir / "follow_up_backlog.csv").exists()
    with zipfile.ZipFile(out_zip) as zf:
        names = set(zf.namelist())
    assert "s13l_completed_review_results_ingest_manifest.json" in names
    assert "scenario_review_decisions.json" in names
    assert "completed_worksheets/01_executive_memo_to_board_deck_worksheet.json" in names


def test_s13l_rejects_pending_or_incomplete_review(tmp_path: Path) -> None:
    packet_zip = tmp_path / "s13k-packet.zip"
    review_zip = tmp_path / "review-results.zip"
    _write_packet_zip(packet_zip)
    _write_review_results_zip(review_zip, mutate_first={"decision": "", "review_state": "pending_human_review"})

    report = build_s13l_ingest_report(review_zip, s13k_packet_input=packet_zip, artifacts_dir=tmp_path / "artifacts")

    assert report["status"] == "failed"
    assert any("review_state must be completed_review" in error for error in report["errors"])
    assert any("decision must be one of" in error for error in report["errors"])
    assert report["auto_approval_allowed_by_s13l"] is False


def test_s13l_rejects_missing_salvage_ack_or_digest_mismatch(tmp_path: Path) -> None:
    packet_zip = tmp_path / "s13k-packet.zip"
    review_zip = tmp_path / "review-results.zip"
    _write_packet_zip(packet_zip)
    _write_review_results_zip(
        review_zip,
        mutate_first={
            "salvage_provenance_acknowledgement": False,
            "used_text_to_minimal_model_adapter": False,
            "canonical_payload_digest": "sha256:mismatch",
        },
    )

    report = build_s13l_ingest_report(review_zip, s13k_packet_input=packet_zip, artifacts_dir=tmp_path / "artifacts")

    assert report["status"] == "failed"
    assert any("salvage_provenance_acknowledgement must be true" in error for error in report["errors"])
    assert any("used_text_to_minimal_model_adapter=true" in error for error in report["errors"])
    assert any("canonical_payload_digest does not match" in error for error in report["errors"])
