from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_p10_4_post_p9_human_re_review.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_p10_4_builds_pending_human_re_review_packet() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P10-4"
    assert payload["status"] == "ready"
    assert payload["p10_4_post_p9_human_re_review_capture_supported"] is True
    assert payload["human_re_review_capture_packet_generated_by_p10_4"] is True
    assert payload["human_re_review_completed_by_p10_4"] is False
    assert payload["review_worksheet_count"] == 5
    assert payload["expected_review_worksheet_count"] == 5
    assert payload["all_review_decisions_pending"] is True
    assert payload["approval_state_changed_by_p10_4"] is False
    assert payload["golden_decks_auto_approved_by_p10_4"] is False
    assert payload["kimi_level_claimed_by_p10_4"] is False
    assert payload["whole_project_kimi_level_supported"] is False


def test_p10_4_review_worksheets_require_real_human_decisions() -> None:
    payload = json.loads(run_check("--json", "--require-ready").stdout)
    assert set(payload["allowed_decisions"]) == {"approve", "request_rework", "reject"}
    assert set(payload["required_review_fields"]) == {
        "reviewer_id",
        "reviewed_at",
        "decision",
        "scores",
        "slide_level_findings",
        "follow_up_backlog",
    }
    for worksheet in payload["review_worksheets"]:
        assert worksheet["original_p9_1b_decision"] == "request_rework"
        assert worksheet["post_p9_review_state"] == "pending_human_review"
        assert worksheet["decision"] is None
        assert worksheet["reviewer_id"] is None
        assert worksheet["reviewed_at"] is None
        assert worksheet["requires_human_re_review"] is True
        assert "approval-state change" in worksheet["operator_instruction"]


def test_p10_4_can_persist_review_packet(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "p10_4_review_packet"
    result = run_check("--json", "--require-ready", "--artifacts-dir", str(artifacts_dir))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    packet_path = artifacts_dir / "p10_4_post_p9_human_re_review_packet.json"
    assert packet_path.exists()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["checkpoint"] == "P10-4"
    assert packet["review_worksheet_count"] == 5
    assert packet["human_re_review_completed_by_p10_4"] is False


def test_p10_4_scope_guard_remains_closed() -> None:
    payload = json.loads(run_check("--json", "--require-ready").stdout)
    assert payload["known_non_blocking_warnings_inherited_from_p9"] is True
    assert payload["full_runner_acceptance_mode"] == "pass_with_known_non_blocking_warnings"
    assert payload["npm_audit_fix_force_run_by_p10_4"] is False
    assert payload["api_endpoint_added_by_p10_4"] is False
    assert payload["db_schema_migration_added_by_p10_4"] is False
    assert payload["frontend_runtime_changed_by_p10_4"] is False
    assert payload["dependency_versions_changed_by_p10_4"] is False
    assert payload["dockerfiles_changed_by_p10_4"] is False
    assert payload["cloud_llm_added_by_p10_4"] is False
    assert payload["cloud_vision_added_by_p10_4"] is False
    assert payload["network_required"] is False
