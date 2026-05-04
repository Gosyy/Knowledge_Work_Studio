from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_rc1_golden_benchmark_harness_executes_all_k0_cases(tmp_path: Path) -> None:
    root = repo_root()
    artifacts_dir = tmp_path / "rc1-artifacts"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_rc1_golden_benchmark_harness.py",
            "--repo-root",
            str(root),
            "--artifacts-dir",
            str(artifacts_dir),
            "--json",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)

    assert report["checkpoint"] == "RC1"
    assert report["status"] == "ready"
    assert report["golden_benchmark_execution_harness_supported"] is True
    assert report["k0_golden_cases_executed"] == 5
    assert report["k0_golden_cases_passed"] == 5
    assert report["all_golden_cases_passed"] is True
    assert report["k6_workflow_used_for_each_case"] is True
    assert report["pptx_artifacts_generated"] is True
    assert report["manifest_artifacts_generated"] is True
    assert report["source_to_slide_provenance_verified"] is True
    assert report["visual_qa_executed"] is True
    assert report["human_benchmark_review_required"] is True
    assert report["k_phase_closure_commit_is_ancestor"] is True
    assert report["kimi_level_claimed_by_rc1"] is False
    assert report["whole_project_kimi_level_supported"] is False
    assert report["network_required"] is False
    assert report["api_endpoint_added_by_rc1"] is False
    assert report["db_schema_migration_added_by_rc1"] is False
    assert report["frontend_runtime_changed_by_rc1"] is False
    assert report["dependency_versions_changed_by_rc1"] is False
    assert report["dockerfiles_changed_by_rc1"] is False
    assert report["cloud_llm_added_by_rc1"] is False
    assert report["cloud_vision_added_by_rc1"] is False
    assert report["errors"] == []

    for case in report["case_results"]:
        assert case["status"] == "passed"
        assert case["actual_slide_count"] == case["target_slide_count"]
        assert case["artifact_size_bytes"] > 0
        assert case["artifact_checksum_sha256"].startswith("sha256:")
        assert case["provenance_coverage_status"] == "complete"
        assert case["passed_gate_count"] == case["gate_count"]
        assert case["automated_proxy_kimi_level_candidate_passed"] is False
        generated = set(case["generated_artifact_paths"])
        assert f"{case['case_id']}/manifest.json" in generated
        assert f"{case['case_id']}/safe_metadata.json" in generated
        assert f"{case['case_id']}/{case['artifact_filename']}" in generated
        assert (artifacts_dir / case["case_id"] / case["artifact_filename"]).exists()


def test_rc1_require_ready_accepts_commits_after_k_phase_closure(tmp_path: Path) -> None:
    root = repo_root()
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_rc1_golden_benchmark_harness.py",
            "--repo-root",
            str(root),
            "--artifacts-dir",
            str(tmp_path / "rc1-require-ready-artifacts"),
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
    report = json.loads(result.stdout)
    assert report["status"] == "ready"
    assert report["k_phase_closure_commit_is_ancestor"] is True
    assert report["all_golden_cases_passed"] is True
    assert report["whole_project_kimi_level_supported"] is False
