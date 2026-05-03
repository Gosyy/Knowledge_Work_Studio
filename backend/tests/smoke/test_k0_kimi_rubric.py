from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.k_phase import build_k0_rubric_report, score_candidate_dimension_scores


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run([sys.executable, "scripts/kw_k0_kimi_rubric_check.py", "--repo-root", str(root), *args], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def test_k0_checker_reports_ready_without_kimi_overclaim() -> None:
    result = run_check("--require-ready", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["mode"] == "k0-kimi-level-rubric-golden-benchmark"
    assert payload["checkpoint"] == "K0"
    assert payload["k_phase_branch"] == "8_K_Phase"
    assert payload["status"] == "ready"
    assert payload["k_phase_started_by_k0"] is True
    assert payload["k0_is_evaluation_only"] is True
    assert payload["k0_rubric_defined"] is True
    assert payload["golden_benchmark_defined"] is True
    assert payload["runtime_changed_by_k0"] is False
    assert payload["dependency_versions_changed_by_k0"] is False
    assert payload["dockerfiles_changed_by_k0"] is False
    assert payload["api_endpoint_added_by_k0"] is False
    assert payload["db_schema_migration_added_by_k0"] is False
    assert payload["kimi_level_claimed_by_k0"] is False
    assert payload["whole_project_kimi_level_supported"] is False


def test_k0_rubric_has_weighted_dimensions_and_golden_cases() -> None:
    report = build_k0_rubric_report().as_dict()
    dimensions = report["rubric_dimensions"]
    cases = report["golden_benchmark_cases"]
    assert report["status"] == "ready"
    assert len(dimensions) == 10
    assert sum(item["weight"] for item in dimensions) == 100
    assert len(cases) == 5
    assert {case["source_kind"] for case in cases} == {"memo", "technical_document", "project_log", "comparison_table", "long_docx_pdf"}


def test_k0_scoring_contract_accepts_strong_future_candidate_but_rejects_weak_source_grounding() -> None:
    report = build_k0_rubric_report().as_dict()
    strong_scores = {item["dimension_id"]: 90 for item in report["rubric_dimensions"]}
    weak_scores = dict(strong_scores)
    weak_scores["source_faithfulness"] = 30
    assert score_candidate_dimension_scores(strong_scores)["kimi_level_candidate_passed"] is True
    rejected = score_candidate_dimension_scores(weak_scores)
    assert rejected["kimi_level_candidate_passed"] is False
    assert any("source_faithfulness" in error for error in rejected["errors"])
    assert rejected["kimi_level_claimed"] is False


def test_k0_production_readiness_gate_mentions_checkpoint() -> None:
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")
    assert "K0 Kimi-level rubric and golden benchmark" in gate
    assert "scripts/kw_k0_kimi_rubric_check.py" in gate
    assert "docs/codex/K0_KIMI_LEVEL_RUBRIC_AND_GOLDEN_BENCHMARK.md" in gate
