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
        [sys.executable, "scripts/kw_p10_3_post_p9_artifact_comparison.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_p10_3_compares_post_p9_artifacts_against_original_findings() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P10-3"
    assert payload["status"] == "ready"
    assert payload["p10_3_post_p9_artifact_comparison_supported"] is True
    assert payload["post_p9_artifacts_compared_to_p9_1b_findings"] is True
    assert payload["comparison_case_count"] == 5
    assert payload["original_request_rework_count"] == 5
    assert payload["original_approve_count"] == 0
    assert payload["human_re_review_required_after_p10_3"] is True
    assert payload["approval_state_changed_by_p10_3"] is False
    assert payload["golden_decks_auto_approved_by_p10_3"] is False


def test_p10_3_case_cards_preserve_original_blockers_and_generated_evidence() -> None:
    result = run_check("--json", "--require-ready")
    payload = json.loads(result.stdout)
    cards = payload["case_comparison_cards"]
    assert len(cards) == 5
    assert any(card["original_blocker_finding_count"] > 0 for card in cards)
    for card in cards:
        assert card["original_decision"] == "request_rework"
        assert card["post_p9_artifact_present"] is True
        assert card["post_p9_pptx_size_bytes"] > 0
        assert card["post_p9_manifest_digest"].startswith("sha256:")
        assert card["post_p9_safe_metadata_digest"].startswith("sha256:")
        assert card["requires_human_re_review"] is True
        assert "Compare this generated artifact" in card["comparison_instruction"]


def test_p10_3_scope_guard_and_no_kimi_claim() -> None:
    result = run_check("--json", "--require-ready")
    payload = json.loads(result.stdout)
    assert payload["known_non_blocking_warnings_inherited_from_p9"] is True
    assert payload["full_runner_acceptance_mode"] == "pass_with_known_non_blocking_warnings"
    assert payload["npm_audit_fix_force_run_by_p10_3"] is False
    assert payload["api_endpoint_added_by_p10_3"] is False
    assert payload["db_schema_migration_added_by_p10_3"] is False
    assert payload["frontend_runtime_changed_by_p10_3"] is False
    assert payload["dependency_versions_changed_by_p10_3"] is False
    assert payload["dockerfiles_changed_by_p10_3"] is False
    assert payload["cloud_llm_added_by_p10_3"] is False
    assert payload["cloud_vision_added_by_p10_3"] is False
    assert payload["kimi_level_claimed_by_p10_3"] is False
    assert payload["whole_project_kimi_level_supported"] is False
    assert payload["network_required"] is False
