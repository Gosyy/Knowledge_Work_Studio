#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "docs/codex/SLIDES_RUNTIME_RF2_FINAL_CLOSURE.md",
    "backend/app/services/slides_service/rf2_final_closure.py",
    "scripts/kw_slides_rf2_closure_check.py",
    "backend/tests/smoke/test_rf2_closure_slides_runtime.py",
    "docs/codex/SLIDES_RUNTIME_RF2_CLOSURE.md",
    "backend/app/services/slides_service/runtime_closure.py",
    "scripts/kw_slides_runtime_closure_check.py",
    "backend/tests/smoke/test_rf2_7_slides_runtime_closure.py",
    "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md",
    "docs/codex/RUNTIME_FOUNDATION_PHASE_PLAN.md",
    "scripts/kw_production_readiness_gate.py",
    "backend/app/services/slides_service/__init__.py",
    "scripts/kw_slides_runtime_phase_check.py",
    "scripts/kw_slides_runtime_inventory_check.py",
    "scripts/kw_slides_approved_plan_runtime_check.py",
    "scripts/kw_rf_to_k_transition_check.py",
    "scripts/kw_slides_approved_plan_lifecycle_check.py",
    "scripts/kw_slides_saved_plan_retry_check.py",
    "scripts/kw_slides_render_mode_runtime_check.py",
    "scripts/kw_slides_provenance_manifest_runtime_check.py",
)

REQUIRED_MARKERS = {
    "final_closure_doc_title": ("docs/codex/SLIDES_RUNTIME_RF2_FINAL_CLOSURE.md", "# KW Studio RF2 Final Closure Checkpoint"),
    "final_closure_doc_route": ("docs/codex/SLIDES_RUNTIME_RF2_FINAL_CLOSURE.md", "RF3 -> RF4 -> RF_closure -> K0"),
    "final_closure_doc_no_k": ("docs/codex/SLIDES_RUNTIME_RF2_FINAL_CLOSURE.md", "RF2_closure does not start K-phase."),
    "final_closure_module": ("backend/app/services/slides_service/rf2_final_closure.py", "def build_rf2_final_closure_report("),
    "final_closure_validator": ("backend/app/services/slides_service/rf2_final_closure.py", "def validate_rf2_final_closure_report("),
    "final_closure_export": ("backend/app/services/slides_service/__init__.py", "build_rf2_final_closure_report"),
    "production_gate_step": ("scripts/kw_production_readiness_gate.py", "Slides RF2 final closure checkpoint"),
    "production_gate_file": ("scripts/kw_production_readiness_gate.py", "scripts/kw_slides_rf2_closure_check.py"),
    "phase_plan_next": ("docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md", "RF2_closure accepted next route: RF3 -> RF4 -> RF_closure -> K0"),
    "runtime_foundation_next": ("docs/codex/RUNTIME_FOUNDATION_PHASE_PLAN.md", "RF2_closure accepted next route: RF3 -> RF4 -> RF_closure -> K0"),
}

RF2_CHECKER_COMMANDS = (
    ("RF2.0", "scripts/kw_slides_runtime_phase_check.py", ("--json", "--require-ready")),
    ("RF2.1", "scripts/kw_slides_runtime_inventory_check.py", ("--json", "--require-ready")),
    ("RF2.2", "scripts/kw_slides_approved_plan_runtime_check.py", ("--json", "--require-ready")),
    ("RF2.2a", "scripts/kw_rf_to_k_transition_check.py", ("--json", "--require-ready")),
    ("RF2.3", "scripts/kw_slides_approved_plan_lifecycle_check.py", ("--json", "--require-ready")),
    ("RF2.4", "scripts/kw_slides_saved_plan_retry_check.py", ("--json", "--require-ready")),
    ("RF2.5", "scripts/kw_slides_render_mode_runtime_check.py", ("--json", "--require-ready")),
    ("RF2.6", "scripts/kw_slides_provenance_manifest_runtime_check.py", ("--json", "--require-ready")),
    ("RF2.7", "scripts/kw_slides_runtime_closure_check.py", ("--json", "--require-ready")),
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
            errors.append(f"missing RF2_closure required file: {rel}")

    for name, (rel, marker) in REQUIRED_MARKERS.items():
        if not marker_present(repo_root, rel, marker):
            errors.append(f"missing RF2_closure marker: {name}")

    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        allowed_branches = {"7_Runtime_Foundation", "8_K_Phase", "9_Product_Release_Hardening"}
        if branch not in allowed_branches:
            errors.append(f"expected branch 7_Runtime_Foundation, 8_K_Phase, or 9_Product_Release_Hardening, got {branch}")

    return errors


def _run_checker(repo_root: Path, checkpoint: str, script: str, extra_args: tuple[str, ...]) -> dict[str, Any]:
    command = [sys.executable, script, "--repo-root", str(repo_root), *extra_args]
    result = subprocess.run(
        command,
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    payload: dict[str, Any]
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"raw_stdout": result.stdout[-2000:], "raw_stderr": result.stderr[-2000:]}
    return {
        "checkpoint": checkpoint,
        "script": script,
        "returncode": result.returncode,
        "status": payload.get("status", "unknown"),
        "mode": payload.get("mode", "unknown"),
        "errors": payload.get("errors", []) if isinstance(payload.get("errors", []), list) else [str(payload.get("errors"))],
    }


def run_rf2_checker_smoke(repo_root: Path) -> dict[str, Any]:
    results = [_run_checker(repo_root, checkpoint, script, args) for checkpoint, script, args in RF2_CHECKER_COMMANDS]
    errors: list[str] = []
    for item in results:
        if item["returncode"] != 0 or item["status"] not in {"ready", "accepted"}:
            errors.append(f"{item['checkpoint']} checker failed: {item['script']} status={item['status']} errors={item['errors']}")
    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "all_rf2_checkers_ready": not errors,
        "checker_results": results,
    }


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.slides_service.rf2_final_closure import (
        build_rf2_final_closure_report,
        validate_rf2_final_closure_report,
    )

    report = build_rf2_final_closure_report()
    errors = validate_rf2_final_closure_report(report)
    payload = report.as_dict()
    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "checkpoint": report.checkpoint,
        "closed_checkpoints": list(report.closed_checkpoints),
        "capabilities": list(report.capabilities),
        "rf2_slides_runtime_foundation_closed": report.rf2_slides_runtime_foundation_closed,
        "rf2_slides_path_ready_for_rf3": report.rf2_slides_path_ready_for_rf3,
        "rf3_ready_to_start": report.rf3_ready_to_start,
        "k_phase_started_by_rf2_closure": report.k_phase_started_by_rf2_closure,
        "k_phase_ready_to_start": report.k_phase_ready_to_start,
        "kimi_grade_supported": report.kimi_grade_supported,
        "whole_project_kimi_level_supported": report.whole_project_kimi_level_supported,
        "runtime_changed_by_rf2_closure": report.runtime_changed_by_rf2_closure,
        "dependency_versions_changed_by_rf2_closure": report.dependency_versions_changed_by_rf2_closure,
        "dockerfiles_changed_by_rf2_closure": report.dockerfiles_changed_by_rf2_closure,
        "api_endpoint_added_by_rf2_closure": report.api_endpoint_added_by_rf2_closure,
        "db_schema_migration_added_by_rf2_closure": report.db_schema_migration_added_by_rf2_closure,
        "visual_qa_runtime_added_by_rf2_closure": report.visual_qa_runtime_added_by_rf2_closure,
        "report": payload,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready=require_ready)
    runtime_smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    checker_smoke = run_rf2_checker_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}

    errors = list(static_errors)
    errors.extend(runtime_smoke.get("errors", []))
    errors.extend(checker_smoke.get("errors", []))

    return {
        "mode": "slides-rf2-final-closure-checkpoint",
        "phase": "RF2",
        "checkpoint": "RF2_closure",
        "network_required": False,
        "runtime_changed_by_rf2_closure": False,
        "runtime_change_type": "rf2_final_closure_checkpoint_no_new_runtime_feature",
        "rf2_closed_by_rf2_closure": True,
        "rf2_slides_runtime_foundation_closed": runtime_smoke.get("rf2_slides_runtime_foundation_closed") is True,
        "rf2_slides_path_ready_for_rf3": runtime_smoke.get("rf2_slides_path_ready_for_rf3") is True,
        "all_rf2_checkers_ready": checker_smoke.get("all_rf2_checkers_ready") is True,
        "rf3_ready_to_start": runtime_smoke.get("rf3_ready_to_start") is True,
        "k_phase_started_by_rf2_closure": False,
        "k_phase_ready_to_start": False,
        "dependency_versions_changed_by_rf2_closure": False,
        "dockerfiles_changed_by_rf2_closure": False,
        "frontend_runtime_changed_by_rf2_closure": False,
        "llm_topology_changed_by_rf2_closure": False,
        "browser_runtime_changed_by_rf2_closure": False,
        "api_endpoint_added_by_rf2_closure": False,
        "db_schema_migration_added_by_rf2_closure": False,
        "queue_or_event_store_migration_added_by_rf2_closure": False,
        "provenance_manifest_runtime_already_present_from_rf2_6": True,
        "visual_qa_runtime_added_by_rf2_closure": False,
        "kimi_grade_supported": False,
        "product_grade_supported": False,
        "whole_project_kimi_level_supported": False,
        "runtime_smoke": runtime_smoke,
        "rf2_checker_smoke": checker_smoke,
        "next_recommended_step": "RF3 — Real document ingestion for DOCX and PDF",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RF2 final closure checkpoint check.")
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
