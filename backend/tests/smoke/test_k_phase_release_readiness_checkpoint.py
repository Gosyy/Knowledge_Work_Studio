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
        [sys.executable, "scripts/kw_k_phase_release_readiness_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_k_phase_release_readiness_closes_k0_to_k6_without_feature_scope() -> None:
    result = run_check("--json")
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)

    assert report["checkpoint"] == "K_PHASE_CLOSURE"
    assert report["status"] == "ready"
    assert tuple(report["closed_checkpoints"]) == ("K0", "K1", "K2", "K3", "K4", "K5", "K6")
    assert report["closed_checkpoint_count"] == report["required_checkpoint_count"] == 7
    assert report["k_phase_route_closed"] is True
    assert report["k_phase_ready_for_release_candidate"] is True
    assert report["release_readiness_checkpoint_supported"] is True
    assert report["feature_scope_added_by_k_phase_closure"] is False
    assert report["feature_runtime_added_by_k_phase_closure"] is False
    assert report["api_endpoint_added_by_k_phase_closure"] is False
    assert report["db_schema_migration_added_by_k_phase_closure"] is False
    assert report["frontend_runtime_changed_by_k_phase_closure"] is False
    assert report["dependency_versions_changed_by_k_phase_closure"] is False
    assert report["dockerfiles_changed_by_k_phase_closure"] is False
    assert report["cloud_llm_added_by_k_phase_closure"] is False
    assert report["cloud_vision_added_by_k_phase_closure"] is False
    assert report["kimi_like_workflow_checkpoint_closed"] is True
    assert report["whole_project_kimi_level_supported"] is False
    assert report["kimi_level_claimed_by_k_phase_closure"] is False
    assert report["network_required"] is False
    assert report["errors"] == []
