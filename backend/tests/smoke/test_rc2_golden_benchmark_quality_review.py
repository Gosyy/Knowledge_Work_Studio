from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_rc2_golden_benchmark_quality_review_report_generates_diagnostic_map(tmp_path: Path) -> None:
    root = repo_root()
    artifacts_dir = tmp_path / "rc2-artifacts"
    report_out = tmp_path / "rc2_quality_findings.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_rc2_golden_benchmark_quality_review.py",
            "--repo-root",
            str(root),
            "--artifacts-dir",
            str(artifacts_dir),
            "--report-out",
            str(report_out),
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

    assert report["checkpoint"] == "RC2"
    assert report["status"] == "ready"
    assert report["golden_benchmark_quality_review_supported"] is True
    assert report["rc1_harness_status"] == "ready"
    assert report["k0_golden_cases_reviewed"] == 5
    assert report["all_golden_cases_passed_rc1"] is True
    assert report["quality_diagnosis_generated"] is True
    assert report["quality_diagnosis_is_human_final"] is False
    assert report["human_benchmark_review_required"] is True
    assert report["renderer_findings_generated"] is True
    assert report["provenance_findings_generated"] is True
    assert report["visual_qa_findings_generated"] is True
    assert report["source_faithfulness_findings_generated"] is True
    assert report["workflow_findings_generated"] is True
    assert report["blocking_findings"] == 0
    assert report["warning_findings"] > 0
    assert report["feature_runtime_added_by_rc2"] is False
    assert report["api_endpoint_added_by_rc2"] is False
    assert report["db_schema_migration_added_by_rc2"] is False
    assert report["frontend_runtime_changed_by_rc2"] is False
    assert report["dependency_versions_changed_by_rc2"] is False
    assert report["dockerfiles_changed_by_rc2"] is False
    assert report["cloud_llm_added_by_rc2"] is False
    assert report["cloud_vision_added_by_rc2"] is False
    assert report["kimi_level_claimed_by_rc2"] is False
    assert report["whole_project_kimi_level_supported"] is False
    assert report["network_required"] is False
    assert report["errors"] == []

    areas = {finding["area"] for finding in report["case_quality_findings"]}
    assert {"renderer", "provenance", "visual_qa", "source_faithfulness", "workflow"}.issubset(areas)
    severities = {finding["severity"] for finding in report["case_quality_findings"]}
    assert "warning" in severities
    assert "blocking" not in severities
    assert any("RCH1" in finding["recommended_next_patch"] for finding in report["case_quality_findings"])
    assert any("RCH2" in finding["recommended_next_patch"] for finding in report["case_quality_findings"])
    assert any("RCH3" in finding["recommended_next_patch"] for finding in report["case_quality_findings"])
    assert any("RC3" in finding["recommended_next_patch"] for finding in report["case_quality_findings"])
    assert report_out.exists()
    saved = json.loads(report_out.read_text(encoding="utf-8"))
    assert saved["checkpoint"] == "RC2"
    assert saved["status"] == "ready"
