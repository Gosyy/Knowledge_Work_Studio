from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "kw_p10_11_final_operator_release_closure.py"


def run_checker(*extra: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(REPO_ROOT), "--json", *extra],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def p10_11_report() -> dict:
    return run_checker()


def test_p10_11_closes_release_for_operator_handoff(p10_11_report: dict) -> None:
    report = p10_11_report
    assert report["status"] == "ready"
    assert report["release_decision_from_p10_10"] == "approved_for_release"
    assert report["release_approval_granted_by_p10_10"] is True
    assert report["operator_release_closure_completed_by_p10_11"] is True
    assert report["project_release_status_after_p10_11"] == "approved_for_operator_handoff"
    assert report["approved_golden_case_count_after_p10_11"] == 5
    assert report["request_rework_count_after_p10_11"] == 0
    assert report["reject_count_after_p10_11"] == 0
    assert report["blocking_case_ids_after_p10_11"] == []


def test_p10_11_preserves_operator_logging_and_profile_rules(p10_11_report: dict) -> None:
    report = p10_11_report
    assert report["operator_logs_must_stay_in_repo_logs"] is True
    assert report["downloads_are_handoff_only"] is True
    assert report["assistant_must_locally_apply_and_test_future_patches"] is True
    assert report["handoff_profile_1_project_path"] == "/home/su4ka/workplace/Knowledge_Work_Studio"
    assert report["handoff_profile_2_project_path"] == "/home/editor/workplace/Knowledge_Work_Studio"


def test_p10_11_preserves_gigachat_and_kimi_boundaries(p10_11_report: dict) -> None:
    report = p10_11_report
    assert report["project_completion_can_use_public_api_dev_gigachat_evidence"] is True
    assert report["p10_5a_public_api_dev_evidence_is_real_provider_evidence"] is True
    assert report["p10_5a_public_api_dev_evidence_is_not_server3_offline_proof"] is True
    assert report["server3_local_intranet_route_verified_by_p10_11"] is False
    assert report["production_offline_mode_remains_target_deployment_mode"] is True
    assert report["kimi_level_claimed_by_p10_11"] is False
    assert report["whole_project_kimi_level_supported"] is False


def test_p10_11_can_persist_closure(tmp_path: Path) -> None:
    out_dir = tmp_path / "p10-11"
    report = run_checker("--artifacts-dir", str(out_dir))
    closure_path = Path(report["p10_11_closure_file"])
    assert closure_path.exists()
    persisted = json.loads(closure_path.read_text(encoding="utf-8"))
    assert persisted["p10_11_closure_digest"].startswith("sha256:")
    assert persisted["project_release_status_after_p10_11"] == "approved_for_operator_handoff"
