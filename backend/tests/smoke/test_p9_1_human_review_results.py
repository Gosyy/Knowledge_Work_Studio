from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_p9_1b_human_review_results_capture_reports_ready(tmp_path: Path) -> None:
    root = repo_root()
    artifacts_dir = tmp_path / "p9-1b"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_p9_1_human_review_results_check.py",
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
    assert payload["checkpoint"] == "P9-1B"
    assert payload["status"] == "ready"
    assert payload["source_baseline_commit"] == "a2f1aa90fbc56531de85a953447f61a52a63efb7"
    assert payload["human_review_results_tracked"] is True
    assert payload["human_review_results_completed"] is True
    assert payload["reviewed_case_count"] == 5
    assert payload["decision_counts"] == {"approve": 0, "reject": 0, "request_rework": 5}
    assert payload["request_rework_case_count"] == 5
    assert payload["approve_case_count"] == 0
    assert payload["reject_case_count"] == 0
    assert payload["follow_up_backlog_item_count"] >= 10
    assert payload["review_results_digest"].startswith("sha256:")
    assert payload["kimi_level_claimed"] is False
    assert payload["whole_project_kimi_level_supported"] is False
    assert payload["api_endpoint_added_by_p9_1b"] is False
    assert payload["db_schema_migration_added_by_p9_1b"] is False
    assert payload["frontend_runtime_changed_by_p9_1b"] is False
    assert payload["dependency_versions_changed_by_p9_1b"] is False
    assert payload["dockerfiles_changed_by_p9_1b"] is False
    assert payload["cloud_llm_added_by_p9_1b"] is False
    assert payload["cloud_vision_added_by_p9_1b"] is False
    assert payload["product_runtime_changed_by_p9_1b"] is False
    assert (artifacts_dir / "p9-1b-human-review-results-capture.json").exists()
    assert (artifacts_dir / "p9-1b-follow-up-backlog.json").exists()


def test_p9_1b_tracked_review_json_is_complete_and_conservative() -> None:
    root = repo_root()
    review_path = root / "backend/tests/fixtures/p9/p9_1_human_review_results.json"
    payload = json.loads(review_path.read_text(encoding="utf-8"))
    assert payload["status"] == "completed_human_review"
    assert payload["human_review_results_completed"] is True
    assert payload["kimi_level_claimed"] is False
    assert payload["whole_project_kimi_level_supported"] is False
    assert len(payload["cases"]) == 5
    assert all(item["review_status"] == "completed" for item in payload["cases"])
    assert all(item["decision"] == "request_rework" for item in payload["cases"])
    assert all(item["follow_up_backlog"] for item in payload["cases"])
