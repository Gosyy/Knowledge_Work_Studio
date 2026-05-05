from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_rc4_release_candidate_artifact_pack_reports_ready(tmp_path: Path) -> None:
    root = repo_root()
    artifacts_dir = tmp_path / "rc4-pack"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_rc4_release_candidate_artifact_pack.py",
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

    assert payload["checkpoint"] == "RC4"
    assert payload["status"] == "ready"
    assert payload["release_candidate_artifact_pack_supported"] is True
    assert payload["artifact_inventory_supported"] is True
    assert payload["machine_readable_pack_manifest_supported"] is True
    assert payload["operator_release_notes_supported"] is True
    assert payload["known_limitations_tracked"] is True
    assert payload["human_benchmark_review_required"] is True
    assert payload["offline_safe_default_required"] is True
    assert payload["server3_offline_route_verification_required_before_production_claim"] is True
    assert payload["pack_item_count"] >= 14
    assert payload["artifact_file_count"] == payload["pack_item_count"] * 3
    assert payload["artifact_inventory_digest"].startswith("sha256:")
    assert payload["errors"] == []

    phases = {item["phase"] for item in payload["artifact_inventory"]}
    assert {"K0", "K1", "K2", "K3", "K4", "K5", "K6", "RC1", "RC2", "RC3", "RCH1", "RCH2", "RCH3"}.issubset(phases)

    for item in payload["artifact_inventory"]:
        for file_record in item["files"]:
            assert file_record["exists"] is True
            assert file_record["size_bytes"] > 0
            assert file_record["digest"].startswith("sha256:")

    assert payload["api_endpoint_added_by_rc4"] is False
    assert payload["db_schema_migration_added_by_rc4"] is False
    assert payload["frontend_runtime_changed_by_rc4"] is False
    assert payload["dependency_versions_changed_by_rc4"] is False
    assert payload["dockerfiles_changed_by_rc4"] is False
    assert payload["cloud_llm_added_by_rc4"] is False
    assert payload["cloud_vision_added_by_rc4"] is False
    assert payload["product_runtime_changed_by_rc4"] is False
    assert payload["kimi_level_claimed_by_rc4"] is False
    assert payload["whole_project_kimi_level_supported"] is False

    outputs = payload["artifact_pack_outputs"]
    assert Path(outputs["json"]).exists()
    assert Path(outputs["markdown"]).exists()
    assert "RC4 Release Candidate Artifact Pack" in Path(outputs["markdown"]).read_text(encoding="utf-8")
