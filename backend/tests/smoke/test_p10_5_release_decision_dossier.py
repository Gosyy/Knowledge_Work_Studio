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
        [sys.executable, "scripts/kw_p10_5_release_decision_dossier.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_p10_5_builds_deferred_release_decision_dossier() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P10-5"
    assert payload["status"] == "ready"
    assert payload["release_decision"] == "defer_pending_human_re_review"
    assert payload["release_approval_granted_by_p10_5"] is False
    assert payload["release_decision_is_deferred"] is True
    assert payload["completed_human_review_decision_count"] == 0
    assert payload["pending_human_review_decision_count"] == 5
    assert payload["human_re_review_completed"] is False


def test_p10_5_can_persist_release_dossier(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "p10_5_release_dossier"
    result = run_check("--json", "--require-ready", "--artifacts-dir", str(artifacts_dir))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["release_dossier_persisted"] is True
    dossier_path = artifacts_dir / "p10_5_release_decision_dossier.json"
    assert dossier_path.exists()
    dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
    assert dossier["release_decision"] == "defer_pending_human_re_review"
    assert dossier["golden_decks_auto_approved_by_p10_5"] is False


def test_p10_5_preserves_scope_boundaries() -> None:
    result = run_check("--json", "--require-ready")
    payload = json.loads(result.stdout)
    dossier = payload["release_decision_dossier"]
    assert dossier["approval_state_changed_by_p10_5"] is False
    assert dossier["golden_decks_auto_approved_by_p10_5"] is False
    assert dossier["kimi_level_claimed_by_p10_5"] is False
    assert dossier["whole_project_kimi_level_supported"] is False
    assert dossier["p10_5a_public_api_dev_is_not_server3_offline_proof"] is True
    assert dossier["server3_offline_intranet_route_verified_by_p10_5"] is False
    assert dossier["npm_audit_fix_force_run_by_p10_5"] is False
    assert dossier["dependency_versions_changed_by_p10_5"] is False
    assert dossier["network_required_for_p10_5_static_dossier"] is False
