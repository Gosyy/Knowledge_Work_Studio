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
        [sys.executable, "scripts/kw_p10_1_post_p9_regeneration_readiness_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_p10_1_checker_reports_ready_without_scope_escape() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P10-1"
    assert payload["status"] == "ready"
    assert payload["p10_post_p9_phase_started"] is True
    assert payload["p10_1_post_p9_regeneration_readiness_supported"] is True
    assert payload["post_p9_golden_benchmark_regeneration_required"] is True
    assert payload["post_p9_artifact_pack_generation_performed_by_p10_1"] is False
    assert payload["human_re_review_required_after_regeneration"] is True
    assert payload["approval_state_changed_by_p10_1"] is False
    assert payload["golden_decks_auto_approved_by_p10_1"] is False
    assert payload["api_endpoint_added_by_p10_1"] is False
    assert payload["db_schema_migration_added_by_p10_1"] is False
    assert payload["frontend_runtime_changed_by_p10_1"] is False
    assert payload["dependency_versions_changed_by_p10_1"] is False
    assert payload["dockerfiles_changed_by_p10_1"] is False
    assert payload["cloud_llm_added_by_p10_1"] is False
    assert payload["cloud_vision_added_by_p10_1"] is False
    assert payload["kimi_level_claimed_by_p10_1"] is False
    assert payload["whole_project_kimi_level_supported"] is False


def test_p10_1_regeneration_plan_preserves_five_request_rework_cases() -> None:
    result = run_check("--json", "--require-ready")
    payload = json.loads(result.stdout)
    assert payload["golden_case_count"] == 5
    assert payload["expected_artifact_triplet_count"] == 15
    assert payload["source_fixture_case_ids_match_human_review_cases"] is True
    assert payload["original_request_rework_count"] == 5
    assert payload["original_approve_count"] == 0
    case_ids = set(payload["regeneration_case_ids"])
    assert case_ids == {
        "k0_exec_memo_to_board_deck",
        "k0_arch_doc_to_architecture_deck",
        "k0_project_log_to_status_deck",
        "k0_comparison_table_to_decision_deck",
        "k0_long_docx_pdf_to_structured_presentation",
    }
    for case in payload["regeneration_cases"]:
        assert case["original_human_review_decision"] == "request_rework"
        assert case["requires_human_re_review"] is True
        assert len(case["expected_outputs"]) == 3


def test_p10_1_inherits_warning_classification_without_dependency_remediation() -> None:
    result = run_check("--json", "--require-ready")
    payload = json.loads(result.stdout)
    assert payload["full_runner_acceptance_mode"] == "pass_with_known_non_blocking_warnings"
    assert payload["known_non_blocking_warnings_inherited_from_p9"] is True
    assert payload["dependency_security_remediation_deferred_to_controlled_track"] is True
    assert payload["npm_audit_fix_force_run_by_p10_1"] is False
    assert payload["dependency_versions_changed_by_p10_1"] is False
