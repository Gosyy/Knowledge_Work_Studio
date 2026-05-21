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
        [sys.executable, "scripts/kw_p10_5a_gigachat_api_golden_benchmark.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_p10_5a_static_contract_is_ready_without_credentials() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P10-5a"
    assert payload["status"] == "ready"
    assert payload["live_gigachat_api_run_performed_by_p10_5a"] is False
    assert payload["gigachat_provider_route"] == "public_api_dev"
    assert payload["public_api_dev_route_required_by_p10_5a"] is True
    assert payload["public_api_dev_route_is_not_production_evidence"] is True
    assert payload["production_route_verified_by_p10_5a"] is False
    assert payload["offline_intranet_route_verified_by_p10_5a"] is False


def test_p10_5a_preserves_review_and_scope_boundaries() -> None:
    result = run_check("--json", "--require-ready")
    payload = json.loads(result.stdout)
    assert payload["human_re_review_required_after_p10_5a"] is True
    assert payload["approval_state_changed_by_p10_5a"] is False
    assert payload["golden_decks_auto_approved_by_p10_5a"] is False
    assert payload["kimi_level_claimed_by_p10_5a"] is False
    assert payload["whole_project_kimi_level_supported"] is False
    assert payload["npm_audit_fix_force_run_by_p10_5a"] is False
    assert payload["dependency_versions_changed_by_p10_5a"] is False
    assert payload["dockerfiles_changed_by_p10_5a"] is False


def test_p10_5a_live_requirement_fails_without_live_flag() -> None:
    result = run_check("--json", "--require-ready", "--require-gigachat-used")
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert any("requires --live" in error for error in payload["errors"])
