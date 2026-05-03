#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/K0_KIMI_LEVEL_RUBRIC_AND_GOLDEN_BENCHMARK.md",
    "backend/app/services/k_phase/__init__.py",
    "backend/app/services/k_phase/kimi_level_rubric.py",
    "scripts/kw_k0_kimi_rubric_check.py",
    "backend/tests/smoke/test_k0_kimi_rubric.py",
)

REQUIRED_MARKERS = {
    "k0_doc_no_claim": ("docs/codex/K0_KIMI_LEVEL_RUBRIC_AND_GOLDEN_BENCHMARK.md", "K0 does not claim that KW Studio already reaches Kimi-level."),
    "k0_service_report": ("backend/app/services/k_phase/kimi_level_rubric.py", "def build_k0_rubric_report"),
    "k0_service_score_helper": ("backend/app/services/k_phase/kimi_level_rubric.py", "def score_candidate_dimension_scores"),
    "k0_branch": ("backend/app/services/k_phase/kimi_level_rubric.py", "K_PHASE_BRANCH = \"8_K_Phase\""),
    "k0_gate": ("scripts/kw_production_readiness_gate.py", "K0 Kimi-level rubric and golden benchmark"),
}


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def marker_present(repo_root: Path, rel: str, marker: str) -> bool:
    path = repo_root / rel
    return path.exists() and marker in path.read_text(encoding="utf-8")


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing K0 required file: {rel}")
    for name, (rel, marker) in REQUIRED_MARKERS.items():
        if not marker_present(repo_root, rel, marker):
            errors.append(f"missing K0 marker: {name}")
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch != "8_K_Phase":
            errors.append(f"expected branch 8_K_Phase, got {branch}")
    return errors


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from backend.app.services.k_phase import build_k0_rubric_report, score_candidate_dimension_scores
    report = build_k0_rubric_report().as_dict()
    strong_scores = {str(item["dimension_id"]): 90 for item in report["rubric_dimensions"]}
    weak_scores = dict(strong_scores)
    weak_scores["source_faithfulness"] = 40
    strong = score_candidate_dimension_scores(strong_scores)
    weak = score_candidate_dimension_scores(weak_scores)
    errors: list[str] = []
    if report["status"] != "ready":
        errors.append("K0 rubric report is not ready")
    if report["kimi_level_claimed_by_k0"] is not False:
        errors.append("K0 must not claim Kimi-level")
    if report["whole_project_kimi_level_supported"] is not False:
        errors.append("K0 must not claim whole-project Kimi-level support")
    if len(report["rubric_dimensions"]) != 10:
        errors.append("K0 must expose 10 rubric dimensions")
    if sum(int(item["weight"]) for item in report["rubric_dimensions"]) != 100:
        errors.append("K0 rubric weights must sum to 100")
    if len(report["golden_benchmark_cases"]) != 5:
        errors.append("K0 must expose 5 golden benchmark cases")
    if strong["kimi_level_candidate_passed"] is not True:
        errors.append("strong candidate scoring contract should pass")
    if weak["kimi_level_candidate_passed"] is not False:
        errors.append("weak source faithfulness score should fail")
    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "k0_rubric_defined": report["k0_rubric_defined"],
        "golden_benchmark_defined": report["golden_benchmark_defined"],
        "rubric_dimension_count": len(report["rubric_dimensions"]),
        "rubric_weight_sum": sum(int(item["weight"]) for item in report["rubric_dimensions"]),
        "golden_benchmark_case_count": len(report["golden_benchmark_cases"]),
        "acceptance_gate_count": len(report["acceptance_gates"]),
        "future_strong_candidate_passes_scoring_contract": strong["kimi_level_candidate_passed"],
        "weak_source_faithfulness_rejected": weak["kimi_level_candidate_passed"] is False,
        "kimi_level_claimed_by_k0": report["kimi_level_claimed_by_k0"],
        "whole_project_kimi_level_supported": report["whole_project_kimi_level_supported"],
        "runtime_changed_by_k0": report["runtime_changed_by_k0"],
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready=require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = list(static_errors)
    errors.extend(smoke.get("errors", []))
    return {
        "mode": "k0-kimi-level-rubric-golden-benchmark",
        "phase": "K-phase",
        "checkpoint": "K0",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "rf_closure_required_base": "a52f038b0fb651e3b33c33f999ca9ba0d615bff9",
        "k_phase_branch": "8_K_Phase",
        "k_phase_started_by_k0": True,
        "k0_is_evaluation_only": True,
        "k0_rubric_defined": smoke.get("k0_rubric_defined", False),
        "golden_benchmark_defined": smoke.get("golden_benchmark_defined", False),
        "runtime_changed_by_k0": False,
        "dependency_versions_changed_by_k0": False,
        "dockerfiles_changed_by_k0": False,
        "api_endpoint_added_by_k0": False,
        "db_schema_migration_added_by_k0": False,
        "visual_qa_runtime_added_by_k0": False,
        "cloud_llm_added_by_k0": False,
        "kimi_level_claimed_by_k0": False,
        "whole_project_kimi_level_supported": False,
        "runtime_smoke": smoke,
        "next_recommended_step": "K1 — Local GigaChat planning engine",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio K0 Kimi-level rubric and golden benchmark check.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    report = build_report(repo_root, require_ready=args.require_ready)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 2

if __name__ == "__main__":
    raise SystemExit(main())
