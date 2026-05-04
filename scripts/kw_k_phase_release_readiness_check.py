#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

K_PHASE_CLOSURE_CHECKPOINT = "K_PHASE_CLOSURE"
K_PHASE_CLOSURE_SCHEMA_VERSION = "k_phase.release_readiness_checkpoint.v1"
EXPECTED_K6_VERDICT_COMMIT = os.environ.get("K_PHASE_EXPECTED_K6_VERDICT_COMMIT", "6fbd7e03d7019d85078420a4f81966db69b711dc")
K_PHASE_BRANCH = "8_K_Phase"

REQUIRED_FILES = (
    "docs/codex/K_PHASE_PRODUCT_POWER_PLAN.md",
    "docs/codex/K_PHASE_RELEASE_READINESS_CHECKPOINT.md",
    "scripts/kw_k_phase_release_readiness_check.py",
    "backend/tests/smoke/test_k_phase_release_readiness_checkpoint.py",
    "docs/codex/K0_KIMI_LEVEL_RUBRIC_AND_GOLDEN_BENCHMARK.md",
    "docs/codex/K1_LOCAL_GIGACHAT_PLANNING_ENGINE.md",
    "docs/codex/K2_PLAN_EDITOR_PRODUCT_WORKFLOW.md",
    "docs/codex/K3_RENDERER_QUALITY_RUNTIME.md",
    "docs/codex/K4_VISUAL_QA_RUNTIME.md",
    "docs/codex/K5_SOURCE_TO_SLIDE_PROVENANCE.md",
    "docs/codex/K6_END_TO_END_KIMI_LIKE_WORKFLOW.md",
    "backend/app/services/k_phase/kimi_level_rubric.py",
    "backend/app/services/k_phase/local_gigachat_planner.py",
    "backend/app/services/k_phase/plan_editor.py",
    "backend/app/services/k_phase/renderer_quality.py",
    "backend/app/services/k_phase/visual_qa.py",
    "backend/app/services/k_phase/source_to_slide_provenance.py",
    "backend/app/services/k_phase/end_to_end_workflow.py",
    "scripts/kw_k0_kimi_rubric_check.py",
    "scripts/kw_k1_local_gigachat_planner_check.py",
    "scripts/kw_k2_plan_editor_check.py",
    "scripts/kw_k3_renderer_quality_check.py",
    "scripts/kw_k4_visual_qa_check.py",
    "scripts/kw_k5_source_to_slide_provenance_check.py",
    "scripts/kw_k6_end_to_end_workflow_check.py",
)

CHECKPOINT_CHECKERS = (
    ("K0", "scripts/kw_k0_kimi_rubric_check.py"),
    ("K1", "scripts/kw_k1_local_gigachat_planner_check.py"),
    ("K2", "scripts/kw_k2_plan_editor_check.py"),
    ("K3", "scripts/kw_k3_renderer_quality_check.py"),
    ("K4", "scripts/kw_k4_visual_qa_check.py"),
    ("K5", "scripts/kw_k5_source_to_slide_provenance_check.py"),
    ("K6", "scripts/kw_k6_end_to_end_workflow_check.py"),
)

FORBIDDEN_CLOSURE_MARKERS = (
    "api_endpoint_added_by_k_phase_closure",
    "db_schema_migration_added_by_k_phase_closure",
    "frontend_runtime_changed_by_k_phase_closure",
    "dependency_versions_changed_by_k_phase_closure",
    "dockerfiles_changed_by_k_phase_closure",
    "cloud_llm_added_by_k_phase_closure",
    "cloud_vision_added_by_k_phase_closure",
    "feature_runtime_added_by_k_phase_closure",
)


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def git_success(repo_root: Path, *args: str) -> bool:
    return subprocess.run(("git", *args), cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0


def run_checker(repo_root: Path, checkpoint: str, checker_rel: str, require_ready: bool) -> dict[str, Any]:
    command = [
        sys.executable,
        checker_rel,
        "--repo-root",
        str(repo_root),
        "--json",
    ]
    if require_ready:
        command.insert(-1, "--require-ready")
    result = subprocess.run(command, cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        return {
            "checkpoint": checkpoint,
            "status": "failed",
            "checker": checker_rel,
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-1200:],
            "stderr_tail": result.stderr[-1200:],
        }
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {
            "checkpoint": checkpoint,
            "status": "failed",
            "checker": checker_rel,
            "returncode": result.returncode,
            "parse_error": str(exc),
            "stdout_tail": result.stdout[-1200:],
        }
    return {"checkpoint": checkpoint, "checker": checker_rel, "status": parsed.get("status"), "report": parsed}


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing K-phase closure required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch is not None and branch != K_PHASE_BRANCH:
            errors.append(f"expected branch {K_PHASE_BRANCH}, got {branch}")
        if git_success(repo_root, "rev-parse", "--git-dir"):
            if not git_success(repo_root, "merge-base", "--is-ancestor", EXPECTED_K6_VERDICT_COMMIT, "HEAD"):
                errors.append(f"K6 verdict commit is not an ancestor of HEAD: {EXPECTED_K6_VERDICT_COMMIT}")
    return errors


def _checker_ready(entry: dict[str, Any]) -> bool:
    return entry.get("status") == "ready" and entry.get("report", {}).get("status") == "ready"


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    static_errors = collect_static_errors(repo_root, require_ready)
    checker_results = [run_checker(repo_root, checkpoint, checker_rel, require_ready) for checkpoint, checker_rel in CHECKPOINT_CHECKERS]
    checker_errors = [
        f"{entry['checkpoint']} checker is not ready: {entry.get('status')}"
        for entry in checker_results
        if not _checker_ready(entry)
    ]

    closed_checkpoints = tuple(entry["checkpoint"] for entry in checker_results if _checker_ready(entry))
    all_checkpoints_ready = len(closed_checkpoints) == len(CHECKPOINT_CHECKERS)
    k6_report = next((entry.get("report", {}) for entry in checker_results if entry.get("checkpoint") == "K6"), {})
    k6_report_text = json.dumps(k6_report, ensure_ascii=False, sort_keys=True).lower()
    errors = static_errors + checker_errors

    if k6_report.get("kimi_level_claimed_by_k6") is not False:
        errors.append("K6 checker must not claim full Kimi-level")
    if k6_report.get("whole_project_kimi_level_supported") is not False:
        errors.append("K6 checker must keep whole_project_kimi_level_supported=false")
    if "offline executive reporting requires" in k6_report_text:
        errors.append("K6 checker leaked raw smoke source text into release readiness report")

    report = {
        "checkpoint": K_PHASE_CLOSURE_CHECKPOINT,
        "schema_version": K_PHASE_CLOSURE_SCHEMA_VERSION,
        "status": "ready" if not errors and all_checkpoints_ready else "failed",
        "branch": run_git(repo_root, "branch", "--show-current"),
        "head": run_git(repo_root, "rev-parse", "HEAD"),
        "origin_head": run_git(repo_root, "rev-parse", f"origin/{K_PHASE_BRANCH}"),
        "expected_k6_verdict_commit": EXPECTED_K6_VERDICT_COMMIT,
        "k6_verdict_commit_is_ancestor": git_success(repo_root, "merge-base", "--is-ancestor", EXPECTED_K6_VERDICT_COMMIT, "HEAD")
        if git_success(repo_root, "rev-parse", "--git-dir")
        else None,
        "closed_checkpoints": closed_checkpoints,
        "closed_checkpoint_count": len(closed_checkpoints),
        "required_checkpoint_count": len(CHECKPOINT_CHECKERS),
        "all_k0_to_k6_checkers_ready": all_checkpoints_ready,
        "release_readiness_checkpoint_supported": True,
        "feature_scope_added_by_k_phase_closure": False,
        "feature_runtime_added_by_k_phase_closure": False,
        "api_endpoint_added_by_k_phase_closure": False,
        "db_schema_migration_added_by_k_phase_closure": False,
        "frontend_runtime_changed_by_k_phase_closure": False,
        "dependency_versions_changed_by_k_phase_closure": False,
        "dockerfiles_changed_by_k_phase_closure": False,
        "cloud_llm_added_by_k_phase_closure": False,
        "cloud_vision_added_by_k_phase_closure": False,
        "k_phase_route_closed": all_checkpoints_ready,
        "k_phase_ready_for_release_candidate": not errors and all_checkpoints_ready,
        "kimi_like_workflow_checkpoint_closed": "K6" in closed_checkpoints,
        "whole_project_kimi_level_supported": False,
        "kimi_level_claimed_by_k_phase_closure": False,
        "network_required": False,
        "checker_results": checker_results,
        "errors": errors,
    }
    for marker in FORBIDDEN_CLOSURE_MARKERS:
        if report.get(marker) is not False:
            report.setdefault("errors", []).append(f"forbidden closure marker not false: {marker}")
    if report["errors"]:
        report["status"] = "failed"
        report["k_phase_ready_for_release_candidate"] = False
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check K-phase K0-K6 release readiness without adding feature scope.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repo_root.resolve(), args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"K-phase release readiness status: {report['status']}")
        print(f"closed checkpoints: {', '.join(report['closed_checkpoints'])}")
        print(f"ready for release candidate: {report['k_phase_ready_for_release_candidate']}")
        if report.get("errors"):
            print("errors:")
            for error in report["errors"]:
                print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
