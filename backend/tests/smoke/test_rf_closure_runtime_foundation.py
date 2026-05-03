from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.runtime_foundation_closure import build_runtime_foundation_closure_report


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run([sys.executable, "scripts/kw_runtime_foundation_closure_check.py", "--repo-root", str(root), *args], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def test_rf_closure_checker_reports_ready_without_starting_k_phase() -> None:
    result = run_check("--require-ready", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["mode"] == "runtime-foundation-final-closure"
    assert payload["checkpoint"] == "RF_closure"
    assert payload["status"] == "ready"
    assert payload["runtime_foundation_closed"] is True
    assert payload["rf0_closed"] is True
    assert payload["rf1_closed"] is True
    assert payload["rf2_closed"] is True
    assert payload["rf3_closed"] is True
    assert payload["rf4_closed"] is True
    assert payload["rf_closure_ready_for_k0"] is True
    assert payload["k_phase_started_by_rf_closure"] is False
    assert payload["whole_project_kimi_level_supported"] is False
    assert payload["errors"] == []


def test_rf_closure_report_preserves_no_runtime_or_dependency_scope() -> None:
    report = build_runtime_foundation_closure_report(repo_root()).as_dict()
    safe = report["safe_metadata"]
    assert safe["runtime_changed_by_rf_closure"] is False
    assert safe["dependency_versions_changed_by_rf_closure"] is False
    assert safe["dockerfiles_changed_by_rf_closure"] is False
    assert safe["api_endpoint_added_by_rf_closure"] is False
    assert safe["db_schema_migration_added_by_rf_closure"] is False
    assert safe["cloud_llm_added_by_rf_closure"] is False
    assert safe["cloud_ocr_added_by_rf_closure"] is False
    assert safe["npm_audit_fix_force_run_by_rf_closure"] is False


def test_rf_closure_production_readiness_gate_mentions_final_closure() -> None:
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")
    assert "Runtime Foundation final closure checkpoint" in gate
    assert "scripts/kw_runtime_foundation_closure_check.py" in gate
    assert "docs/codex/RUNTIME_FOUNDATION_FINAL_CLOSURE.md" in gate
