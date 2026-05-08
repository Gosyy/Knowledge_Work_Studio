from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REVIEW_RESULTS = REPO_ROOT / "backend/tests/fixtures/p10/p10_7_human_review_results.json"


def run_p10_7(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/kw_p10_7_human_review_results_ingest.py", "--repo-root", str(REPO_ROOT), "--json", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def payload_from(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


def test_p10_7_ingests_owner_accepted_review_results_without_approval() -> None:
    result = run_p10_7()
    assert result.returncode == 0, result.stdout + result.stderr
    payload = payload_from(result)
    assert payload["checkpoint"] == "P10-7"
    assert payload["status"] == "ready"
    assert payload["p10_7_completed_human_review_results_ingested"] is True
    assert payload["human_re_review_completed_by_p10_7"] is True
    assert payload["review_results_imported_from_owner_accepted_ai_assisted_review"] is True
    assert payload["completed_human_review_decision_count"] == 5
    assert payload["pending_human_review_decision_count"] == 0
    assert payload["approve_count"] == 4
    assert payload["request_rework_count"] == 1
    assert payload["reject_count"] == 0
    assert payload["blocking_case_ids"] == ["k0_arch_doc_to_architecture_deck"]
    assert payload["release_decision_remains"] == "defer_pending_human_re_review"
    assert payload["release_decision_supported_after_p10_7"] == "defer_pending_review_rework"
    assert payload["release_approval_granted_by_p10_7"] is False
    assert payload["approval_state_changed_by_p10_7"] is False
    assert payload["golden_decks_auto_approved_by_p10_7"] is False
    assert payload["kimi_level_claimed_by_p10_7"] is False
    assert payload["whole_project_kimi_level_supported"] is False
    assert payload["server3_offline_intranet_route_verified_by_p10_7"] is False


def test_p10_7_default_fixture_has_completed_owner_accepted_results() -> None:
    review_payload = json.loads(DEFAULT_REVIEW_RESULTS.read_text(encoding="utf-8"))
    assert review_payload["status"] == "completed_human_review_results"
    assert review_payload["human_re_review_completed"] is True
    assert review_payload["owner_acceptance_recorded"] is True
    assert review_payload["release_approval_granted"] is False
    assert review_payload["approval_state_changed"] is False
    assert review_payload["golden_decks_auto_approved"] is False
    assert review_payload["kimi_level_claimed"] is False
    assert review_payload["server3_offline_intranet_route_verified"] is False
    worksheets = review_payload["review_worksheets"]
    assert len(worksheets) == 5
    assert sum(1 for item in worksheets if item["decision"] == "approve") == 4
    assert sum(1 for item in worksheets if item["decision"] == "request_rework") == 1


def test_p10_7_rejects_incomplete_supplied_results(tmp_path: Path) -> None:
    review_payload = json.loads(DEFAULT_REVIEW_RESULTS.read_text(encoding="utf-8"))
    review_payload["review_worksheets"][0]["decision"] = None
    review_file = tmp_path / "incomplete_p10_7_review.json"
    review_file.write_text(json.dumps(review_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    result = run_p10_7("--review-results", str(review_file))
    assert result.returncode == 1
    payload = payload_from(result)
    assert payload["status"] == "failed"
    assert payload["p10_7_completed_human_review_results_ingested"] is False
    assert payload["release_approval_granted_by_p10_7"] is False
    assert any("P10-7a validator rejected" in error for error in payload["errors"])


def test_p10_7_writes_report_when_artifacts_dir_is_supplied(tmp_path: Path) -> None:
    result = run_p10_7("--artifacts-dir", str(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = payload_from(result)
    report_path = tmp_path / "p10_7_human_review_results_ingest_report.json"
    assert report_path.exists()
    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert written["checkpoint"] == "P10-7"
    assert written["status"] == "ready"
    assert payload["status"] == "ready"
