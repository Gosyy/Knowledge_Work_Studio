from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def run_p10_7a(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/kw_p10_7a_human_review_worksheet_import_validator.py", "--repo-root", str(REPO_ROOT), "--json", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def payload_from(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


def review_dimensions() -> list[str]:
    payload = json.loads((REPO_ROOT / "backend/tests/fixtures/p9/p9_1_human_review_results.json").read_text(encoding="utf-8"))
    return [item["dimension_id"] for item in payload["review_dimensions"]]


def completed_packet(decision: str = "approve", score: int = 4) -> dict:
    scores = {dimension_id: score for dimension_id in review_dimensions()}
    worksheets = []
    for index, case_id in enumerate(
        (
            "k0_exec_memo_to_board_deck",
            "k0_arch_doc_to_architecture_deck",
            "k0_project_log_to_status_deck",
            "k0_comparison_table_to_decision_deck",
            "k0_long_docx_pdf_to_structured_presentation",
        ),
        start=1,
    ):
        worksheets.append(
            {
                "case_id": case_id,
                "reviewer_id": "human-reviewer-1",
                "reviewed_at": f"2026-05-08T13:0{index}:00+02:00",
                "decision": decision,
                "scores": dict(scores),
                "slide_level_findings": [],
                "follow_up_backlog": [] if decision == "approve" else ["Resolve reviewer follow-up before release."],
            }
        )
    return {"review_worksheets": worksheets, "kimi_level_claimed": False, "whole_project_kimi_level_supported": False}


def test_p10_7a_static_contract_self_check_is_conservative() -> None:
    result = run_p10_7a()
    assert result.returncode == 0, result.stdout + result.stderr
    payload = payload_from(result)
    assert payload["checkpoint"] == "P10-7a"
    assert payload["status"] == "ready"
    assert payload["import_mode"] == "static_contract_only"
    assert payload["validator_contract_self_tested"] is True
    assert payload["release_decision_remains"] == "defer_pending_human_re_review"
    assert payload["release_approval_granted_by_p10_7a"] is False
    assert payload["approval_state_changed_by_p10_7a"] is False
    assert payload["golden_decks_auto_approved_by_p10_7a"] is False
    assert payload["kimi_level_claimed_by_p10_7a"] is False
    assert payload["whole_project_kimi_level_supported"] is False
    assert payload["server3_offline_intranet_route_verified_by_p10_7a"] is False


def test_p10_7a_accepts_completed_payload_without_ingesting(tmp_path: Path) -> None:
    review_file = tmp_path / "completed_review.json"
    review_file.write_text(json.dumps(completed_packet(), ensure_ascii=False, indent=2), encoding="utf-8")
    result = run_p10_7a("--review-results", str(review_file))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = payload_from(result)
    assert payload["status"] == "ready"
    assert payload["review_results_importable_by_p10_7a"] is True
    assert payload["completed_human_review_decision_count"] == 5
    assert payload["pending_human_review_decision_count"] == 0
    assert payload["human_re_review_completed"] is True
    assert payload["release_decision_remains"] == "defer_pending_human_re_review"
    assert payload["release_approval_granted_by_p10_7a"] is False


def test_p10_7a_rejects_pending_or_incomplete_payload(tmp_path: Path) -> None:
    packet = completed_packet()
    packet["review_worksheets"][0]["decision"] = None
    packet["review_worksheets"][0]["reviewer_id"] = ""
    review_file = tmp_path / "pending_review.json"
    review_file.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    result = run_p10_7a("--review-results", str(review_file))
    assert result.returncode == 1
    payload = payload_from(result)
    assert payload["status"] == "failed"
    assert any("decision remains pending" in error for error in payload["errors"])
    assert any("reviewer_id" in error for error in payload["errors"])
    assert payload["approval_state_changed_by_p10_7a"] is False


def test_p10_7a_rejects_scope_claims_and_inconsistent_approval(tmp_path: Path) -> None:
    packet = completed_packet(decision="approve", score=2)
    packet["kimi_level_claimed"] = True
    review_file = tmp_path / "bad_claims_review.json"
    review_file.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    result = run_p10_7a("--review-results", str(review_file))
    assert result.returncode == 1
    payload = payload_from(result)
    assert payload["status"] == "failed"
    assert any("kimi_level_claimed=true" in error for error in payload["errors"])
    assert any("approve decision is inconsistent" in error for error in payload["errors"])
    assert payload["server3_offline_intranet_route_verified_by_p10_7a"] is False
    assert payload["npm_audit_fix_force_run_by_p10_7a"] is False

