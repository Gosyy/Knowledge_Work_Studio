#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from backend.app.services.runtime_foundation_closure import build_runtime_foundation_closure_report

    closure = build_runtime_foundation_closure_report(repo_root)
    payload = closure.as_dict()
    safe = dict(payload["safe_metadata"])
    errors = list(payload["errors"])
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        allowed_branches = {"7_Runtime_Foundation", "8_K_Phase"}
        if branch not in allowed_branches:
            errors.append(f"expected branch 7_Runtime_Foundation or 8_K_Phase, got {branch}")
    payload.update({
        "network_required": False,
        "runtime_foundation_closed": safe["runtime_foundation_closed"],
        "rf0_closed": safe["rf0_closed"],
        "rf1_closed": safe["rf1_closed"],
        "rf2_closed": safe["rf2_closed"],
        "rf3_closed": safe["rf3_closed"],
        "rf4_closed": safe["rf4_closed"],
        "rf_closure_ready_for_k0": safe["rf_closure_ready_for_k0"],
        "k_phase_started_by_rf_closure": safe["k_phase_started_by_rf_closure"],
        "k_phase_ready_to_start_after_rf_closure": safe["k_phase_ready_to_start_after_rf_closure"],
        "runtime_changed_by_rf_closure": safe["runtime_changed_by_rf_closure"],
        "dependency_versions_changed_by_rf_closure": safe["dependency_versions_changed_by_rf_closure"],
        "dockerfiles_changed_by_rf_closure": safe["dockerfiles_changed_by_rf_closure"],
        "frontend_runtime_changed_by_rf_closure": safe["frontend_runtime_changed_by_rf_closure"],
        "llm_topology_changed_by_rf_closure": safe["llm_topology_changed_by_rf_closure"],
        "api_endpoint_added_by_rf_closure": safe["api_endpoint_added_by_rf_closure"],
        "db_schema_migration_added_by_rf_closure": safe["db_schema_migration_added_by_rf_closure"],
        "queue_or_event_store_migration_added_by_rf_closure": safe["queue_or_event_store_migration_added_by_rf_closure"],
        "visual_qa_runtime_added_by_rf_closure": safe["visual_qa_runtime_added_by_rf_closure"],
        "cloud_llm_added_by_rf_closure": safe["cloud_llm_added_by_rf_closure"],
        "cloud_ocr_added_by_rf_closure": safe["cloud_ocr_added_by_rf_closure"],
        "npm_audit_fix_force_run_by_rf_closure": safe["npm_audit_fix_force_run_by_rf_closure"],
        "whole_project_kimi_level_supported": safe["whole_project_kimi_level_supported"],
        "next_recommended_step": safe["next_recommended_step"],
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    })
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RF_closure Runtime Foundation final closure check.")
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
