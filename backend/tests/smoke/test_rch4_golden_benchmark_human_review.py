from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_rch4_golden_benchmark_human_review_workflow_reports_ready(tmp_path: Path) -> None:
    root = repo_root()
    artifacts_dir = tmp_path / "rch4-review"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_rch4_golden_benchmark_human_review.py",
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

    assert payload["checkpoint"] == "RCH4"
    assert payload["status"] == "ready"
    assert payload["golden_benchmark_human_review_supported"] is True
    assert payload["human_review_required_before_stronger_quality_claim"] is True
    assert payload["machine_readable_review_template_supported"] is True
    assert payload["slide_level_findings_supported"] is True
    assert payload["follow_up_backlog_supported"] is True
    assert payload["review_case_count"] >= 5
    assert payload["review_dimension_count"] >= 8
    assert payload["review_template_digest"].startswith("sha256:")
    assert payload["errors"] == []

    decisions = set(payload["operator_review_decisions_supported"])
    assert {"approve", "request_rework", "reject"}.issubset(decisions)

    case_ids = {item["case_id"] for item in payload["review_template"]["cases"]}
    assert "k0_exec_memo_to_board_deck" in case_ids
    assert "k0_arch_doc_to_architecture_deck" in case_ids
    assert "k0_long_docx_pdf_to_structured_presentation" in case_ids

    first_case = payload["review_template"]["cases"][0]
    assert first_case["review_status"] == "pending_human_review"
    assert "slide_level_findings" in first_case["required_reviewer_notes"]
    assert "source_faithfulness" in first_case["score_template"]

    assert payload["api_endpoint_added_by_rch4"] is False
    assert payload["db_schema_migration_added_by_rch4"] is False
    assert payload["frontend_runtime_changed_by_rch4"] is False
    assert payload["dependency_versions_changed_by_rch4"] is False
    assert payload["dockerfiles_changed_by_rch4"] is False
    assert payload["cloud_llm_added_by_rch4"] is False
    assert payload["cloud_vision_added_by_rch4"] is False
    assert payload["product_runtime_changed_by_rch4"] is False
    assert payload["kimi_level_claimed_by_rch4"] is False
    assert payload["whole_project_kimi_level_supported"] is False

    outputs = payload["review_outputs"]
    assert Path(outputs["json"]).exists()
    assert Path(outputs["markdown"]).exists()
    assert Path(outputs["worksheet"]).exists()
    assert "RCH4 Golden Benchmark Human Review Workflow" in Path(outputs["markdown"]).read_text(encoding="utf-8")
