from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_krc_final_branch_closure_reports_ready(tmp_path: Path) -> None:
    root = repo_root()
    artifacts_dir = tmp_path / "krc-closure"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_krc_final_branch_closure_check.py",
            "--repo-root",
            str(root),
            "--artifacts-dir",
            str(artifacts_dir),
            "--require-ready",
            "--json",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "KRC"
    assert payload["status"] == "ready"
    assert payload["final_branch_closure_supported"] is True
    assert payload["accepted_release_candidate_baseline"] is True
    assert payload["branch_ready_for_next_phase_planning"] is True
    assert payload["k_phase_checkpoints_closed"] is True
    assert payload["rc_checkpoints_accepted"] is True
    assert payload["rch_checkpoints_accepted"] is True
    assert payload["production_readiness_gate_includes_krc"] is True
    assert payload["closure_item_count"] >= 17
    assert payload["closure_file_count"] == payload["closure_item_count"] * 3 + 3
    assert payload["closure_inventory_digest"].startswith("sha256:")
    assert payload["errors"] == []
    phases = {item["phase"] for item in payload["closure_inventory"]}
    assert {"K0", "K1", "K2", "K3", "K4", "K5", "K6", "RC1", "RC2", "RC3", "RC4", "RC5", "RCH1", "RCH2", "RCH3", "RCH4"}.issubset(phases)
    for item in payload["closure_inventory"]:
        for file_record in item["files"]:
            assert file_record["exists"] is True
            assert file_record["size_bytes"] > 0
            assert file_record["digest"].startswith("sha256:")
    assert payload["human_review_workflow_available"] is True
    assert payload["human_review_judgments_completed_by_krc"] is False
    assert payload["server3_offline_gigachat_verification_completed_by_krc"] is False
    assert payload["dependency_security_remediation_completed_by_krc"] is False
    assert payload["api_endpoint_added_by_krc"] is False
    assert payload["db_schema_migration_added_by_krc"] is False
    assert payload["frontend_runtime_changed_by_krc"] is False
    assert payload["dependency_versions_changed_by_krc"] is False
    assert payload["dockerfiles_changed_by_krc"] is False
    assert payload["cloud_llm_added_by_krc"] is False
    assert payload["cloud_vision_added_by_krc"] is False
    assert payload["product_runtime_changed_by_krc"] is False
    assert payload["kimi_level_claimed_by_krc"] is False
    assert payload["whole_project_kimi_level_supported"] is False
    outputs = payload["closure_outputs"]
    assert Path(outputs["json"]).exists()
    assert Path(outputs["markdown"]).exists()
    assert "K/RC Final Branch Closure" in Path(outputs["markdown"]).read_text(encoding="utf-8")
