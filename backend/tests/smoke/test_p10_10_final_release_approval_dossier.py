from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "kw_p10_10_final_release_approval_dossier.py"


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
def p10_10_report() -> dict:
    return run_checker()


def test_p10_10_grants_release_approval_after_p10_9(p10_10_report: dict) -> None:
    report = p10_10_report
    assert report["status"] == "ready"
    assert report["final_release_decision_by_p10_10"] == "approved_for_release"
    assert report["release_approval_granted_by_p10_10"] is True
    assert report["approve_count_after_p10_9"] == 5
    assert report["request_rework_count_after_p10_9"] == 0
    assert report["reject_count_after_p10_9"] == 0
    assert report["blocking_case_ids_after_p10_9"] == []
    assert report["architecture_request_rework_resolved_by_p10_9"] is True


def test_p10_10_is_not_waiver_based(p10_10_report: dict) -> None:
    report = p10_10_report
    assert report["owner_waiver_used_by_p10_10"] is False
    assert report["release_approval_is_waiver_based"] is False
    assert report["release_approval_requires_additional_human_review"] is False
    assert report["release_approval_requires_targeted_rework"] is False


def test_p10_10_preserves_gigachat_and_offline_boundaries(p10_10_report: dict) -> None:
    report = p10_10_report
    assert report["project_completion_can_use_public_api_dev_gigachat_evidence"] is True
    assert report["p10_5a_public_api_dev_evidence_is_real_provider_evidence"] is True
    assert report["p10_5a_public_api_dev_evidence_is_not_server3_offline_proof"] is True
    assert report["server3_local_intranet_verification_required_for_p10_10"] is False
    assert report["server3_local_intranet_route_verified_by_p10_10"] is False
    assert report["production_offline_mode_remains_target_deployment_mode"] is True
    assert report["network_required_for_p10_10"] is False


def test_p10_10_preserves_no_kimi_or_dependency_scope(p10_10_report: dict) -> None:
    report = p10_10_report
    assert report["kimi_level_claimed_by_p10_10"] is False
    assert report["whole_project_kimi_level_supported"] is False
    assert report["npm_audit_fix_force_run_by_p10_10"] is False
    assert report["dependency_versions_changed_by_p10_10"] is False
    assert report["dockerfiles_changed_by_p10_10"] is False
    assert report["cloud_llm_added_by_p10_10"] is False


def test_p10_10_can_persist_dossier(tmp_path: Path) -> None:
    out_dir = tmp_path / "p10-10"
    report = run_checker("--artifacts-dir", str(out_dir))
    dossier_path = Path(report["p10_10_dossier_file"])
    assert dossier_path.exists()
    persisted = json.loads(dossier_path.read_text(encoding="utf-8"))
    assert persisted["p10_10_dossier_digest"].startswith("sha256:")
    assert persisted["final_release_decision_by_p10_10"] == "approved_for_release"
