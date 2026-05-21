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
        [sys.executable, "scripts/kw_p10_2_post_p9_artifact_pack.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_p10_2_generates_post_p9_artifact_pack_in_temp() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P10-2"
    assert payload["status"] == "ready"
    assert payload["post_p9_artifact_pack_generated_by_p10_2"] is True
    assert payload["artifact_pack_persisted"] is False
    assert payload["golden_case_count"] == 5
    assert payload["artifact_triplet_count"] == 15
    assert payload["human_re_review_required_after_p10_2"] is True
    assert payload["approval_state_changed_by_p10_2"] is False
    assert payload["golden_decks_auto_approved_by_p10_2"] is False
    assert payload["kimi_level_claimed_by_p10_2"] is False
    assert payload["whole_project_kimi_level_supported"] is False
    assert payload["npm_audit_fix_force_run_by_p10_2"] is False
    assert payload["dependency_versions_changed_by_p10_2"] is False


def test_p10_2_can_persist_pack_to_operator_directory(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "post_p9_artifacts"
    result = run_check("--json", "--require-ready", "--artifacts-dir", str(artifacts_dir))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["artifact_pack_persisted"] is True
    manifest = artifacts_dir / "p10_2_post_p9_artifact_pack_manifest.json"
    assert manifest.exists()
    pack_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    assert pack_manifest["checkpoint"] == "P10-2"
    assert pack_manifest["golden_case_count"] == 5
    for card in payload["case_artifact_cards"]:
        for rel_path in card["artifact_paths"]:
            assert (artifacts_dir / rel_path).exists(), rel_path


def test_p10_2_pack_preserves_review_boundaries() -> None:
    result = run_check("--json", "--require-ready")
    payload = json.loads(result.stdout)
    assert payload["known_non_blocking_warnings_inherited_from_p9"] is True
    assert payload["full_runner_acceptance_mode"] == "pass_with_known_non_blocking_warnings"
    assert payload["api_endpoint_added_by_p10_2"] is False
    assert payload["db_schema_migration_added_by_p10_2"] is False
    assert payload["frontend_runtime_changed_by_p10_2"] is False
    assert payload["dockerfiles_changed_by_p10_2"] is False
    assert payload["cloud_llm_added_by_p10_2"] is False
    assert payload["cloud_vision_added_by_p10_2"] is False
    assert payload["network_required"] is False
