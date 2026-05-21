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
        [sys.executable, "scripts/kw_p9_8_product_release_hardening_closure_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_p9_8_checker_reports_ready_without_scope_escape() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P9-8"
    assert payload["status"] == "ready"
    assert payload["p9_8_product_release_hardening_closure_supported"] is True
    assert payload["p9_track_closure_dossier_supported"] is True
    assert payload["p9_phase_count"] == 8
    assert payload["p9_closure_evidence_phase_ids"] == ["P9-1", "P9-2", "P9-3", "P9-4", "P9-5", "P9-6", "P9-7", "P9-8"]
    assert payload["api_endpoint_added_by_p9_8"] is False
    assert payload["db_schema_migration_added_by_p9_8"] is False
    assert payload["frontend_runtime_changed_by_p9_8"] is False
    assert payload["dependency_versions_changed_by_p9_8"] is False
    assert payload["dockerfiles_changed_by_p9_8"] is False
    assert payload["cloud_llm_added_by_p9_8"] is False
    assert payload["cloud_vision_added_by_p9_8"] is False
    assert payload["kimi_level_claimed_by_p9_8"] is False
    assert payload["whole_project_kimi_level_supported"] is False


def test_p9_8_preserves_conservative_human_review_state() -> None:
    result = run_check("--json", "--require-ready")
    payload = json.loads(result.stdout)
    assert payload["golden_case_count"] == 5
    assert payload["original_request_rework_count"] == 5
    assert payload["approval_state_changed_by_p9_8"] is False
    assert payload["human_review_results_fabricated_by_p9_8"] is False
    assert payload["golden_decks_auto_approved_by_p9_8"] is False
    assert payload["post_hardening_human_re_review_required"] is True


def test_p9_8_closure_keeps_known_warning_and_dependency_tracks_separate() -> None:
    result = run_check("--json", "--require-ready")
    payload = json.loads(result.stdout)
    assert payload["full_runner_acceptance_mode"] == "pass_with_known_non_blocking_warnings"
    assert set(payload["known_non_blocking_warning_classes"]) == {
        "npm_deprecated_transitive_packages",
        "npm_audit_vulnerability_summary",
        "rc2_quality_review_warning_findings",
    }
    assert payload["known_non_blocking_full_runner_warning_count"] == 3
    assert payload["dependency_security_remediation_deferred_to_controlled_track"] is True
    assert payload["npm_audit_fix_force_run_by_p9_8"] is False
    assert payload["dependency_versions_changed_by_p9_8"] is False
