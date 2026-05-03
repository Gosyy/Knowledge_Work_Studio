from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.slides_service.rf2_final_closure import (
    RF2_FINAL_NEXT_ROUTE,
    build_rf2_final_closure_report,
    validate_rf2_final_closure_report,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_rf2_closure_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf2_closure_checker_reports_ready_final_checkpoint() -> None:
    result = run_check("--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "slides-rf2-final-closure-checkpoint"
    assert payload["phase"] == "RF2"
    assert payload["checkpoint"] == "RF2_closure"
    assert payload["status"] == "ready"
    assert payload["errors"] == []
    assert payload["rf2_closed_by_rf2_closure"] is True
    assert payload["rf2_slides_runtime_foundation_closed"] is True
    assert payload["rf2_slides_path_ready_for_rf3"] is True
    assert payload["all_rf2_checkers_ready"] is True
    checker_smoke = payload["rf2_checker_smoke"]
    checkpoints = [item["checkpoint"] for item in checker_smoke["checker_results"]]
    assert checkpoints == [
        "RF2.0",
        "RF2.1",
        "RF2.2",
        "RF2.2a",
        "RF2.3",
        "RF2.4",
        "RF2.5",
        "RF2.6",
        "RF2.7",
    ]
    assert all(item["returncode"] == 0 for item in checker_smoke["checker_results"])
    assert payload["rf3_ready_to_start"] is True
    assert payload["k_phase_started_by_rf2_closure"] is False
    assert payload["k_phase_ready_to_start"] is False
    assert payload["runtime_changed_by_rf2_closure"] is False
    assert payload["dependency_versions_changed_by_rf2_closure"] is False
    assert payload["dockerfiles_changed_by_rf2_closure"] is False
    assert payload["api_endpoint_added_by_rf2_closure"] is False
    assert payload["db_schema_migration_added_by_rf2_closure"] is False
    assert payload["visual_qa_runtime_added_by_rf2_closure"] is False
    assert payload["kimi_grade_supported"] is False
    assert payload["whole_project_kimi_level_supported"] is False


def test_rf2_final_closure_report_preserves_route_and_non_goals() -> None:
    report = build_rf2_final_closure_report()
    errors = validate_rf2_final_closure_report(report)

    assert errors == []
    assert report.checkpoint == "RF2_closure"
    assert report.closed_checkpoints == (
        "RF2.0",
        "RF2.1",
        "RF2.2",
        "RF2.2a",
        "RF2.3",
        "RF2.4",
        "RF2.5",
        "RF2.6",
        "RF2.7",
    )
    assert report.next_route == RF2_FINAL_NEXT_ROUTE
    assert report.next_route == ("RF3", "RF4", "RF_closure", "K0")
    assert report.rf2_slides_runtime_foundation_closed is True
    assert report.rf2_closure_is_feature_free_checkpoint is True
    assert report.k_phase_started_by_rf2_closure is False
    assert report.k_phase_ready_to_start is False
    assert report.kimi_grade_supported is False
    assert report.whole_project_kimi_level_supported is False
    assert report.runtime_changed_by_rf2_closure is False


def test_rf2_closure_production_readiness_gate_mentions_final_closure() -> None:
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "Slides RF2 final closure checkpoint" in gate
    assert "scripts/kw_slides_rf2_closure_check.py" in gate
    assert "docs/codex/SLIDES_RUNTIME_RF2_FINAL_CLOSURE.md" in gate
    assert "backend/tests/smoke/test_rf2_closure_slides_runtime.py" in gate
