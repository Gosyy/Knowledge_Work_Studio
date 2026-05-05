#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


REQUIRED_RF2_FILES = (
    "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md",
    "scripts/kw_slides_runtime_phase_check.py",
    "backend/tests/smoke/test_rf2_0_slides_runtime_phase.py",
)

REQUIRED_S_PHASE_SURFACES = (
    "backend/app/services/slides_service/plan_first_contract.py",
    "scripts/kw_slides_plan_first_check.py",
    "scripts/kw_slides_task_events_check.py",
    "scripts/kw_slides_render_modes_check.py",
    "scripts/kw_slides_provenance_manifest_check.py",
    "scripts/kw_slides_plan_editor_check.py",
    "docs/slides-plan-first-ux.md",
    "docs/slides-plan-editor-ui.md",
    "frontend/src/components/presentations/slides-plan-editor-panel.tsx",
    "frontend/tests/e2e/slides-plan-editor-smoke.spec.ts",
)

REQUIRED_RF1_HANDOFF_SURFACES = (
    "docs/codex/OFFLINE_BOOTSTRAP_RF1_CLOSURE.md",
    "docs/codex/OFFLINE_BOOTSTRAP_BUILD_READINESS.md",
    "scripts/kw_offline_bootstrap_bundle_tool.py",
)

REQUIRED_PLAN_PHRASES = (
    "RF2.0 checkpoint",
    "slides runtime phase kickoff",
    "RF2.1 — Slides runtime capability inventory and baseline smoke",
    "RF2.2 — Minimal deterministic PPTX generation from approved plan",
    "RF2.3 — Plan snapshot persistence and task event stream runtime wiring",
    "RF2.4 — Saved-plan retry runtime path",
    "RF2.5 — Adaptive/template local render mode runtime hardening",
    "RF2.6 — Slides provenance manifest emitted as downloadable artifact",
    "Do not start RF2.1 until RF2.0 is accepted.",
    "npm audit fix --force",
    "local GigaChat",
)

FORBIDDEN_RUNTIME_CHANGE_MARKERS = (
    "runtime_changed_by_rf2_0\": true",
    "dependency_versions_changed_by_rf2_0\": true",
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def collect_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_RF2_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing RF2.0 required file: {rel}")

    for rel in REQUIRED_S_PHASE_SURFACES:
        if not (repo_root / rel).exists():
            errors.append(f"missing S-phase slides surface required for RF2 handoff: {rel}")

    for rel in REQUIRED_RF1_HANDOFF_SURFACES:
        if not (repo_root / rel).exists():
            errors.append(f"missing RF1 handoff surface required before RF2: {rel}")

    plan_path = repo_root / "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md"
    if plan_path.exists():
        plan = read_text(plan_path)
        for phrase in REQUIRED_PLAN_PHRASES:
            if phrase not in plan:
                errors.append(f"RF2 phase plan is missing phrase: {phrase}")
        for marker in FORBIDDEN_RUNTIME_CHANGE_MARKERS:
            if marker in plan:
                errors.append(f"RF2.0 plan contains forbidden runtime/dependency marker: {marker}")

    package_json = repo_root / "frontend/package.json"
    package_lock = repo_root / "frontend/package-lock.json"
    requirements = repo_root / "requirements.txt"
    if not package_json.exists():
        errors.append("missing frontend/package.json")
    if not package_lock.exists():
        errors.append("missing frontend/package-lock.json")
    if not requirements.exists():
        errors.append("missing requirements.txt")

    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        allowed_branches = {"7_Runtime_Foundation", "8_K_Phase", "9_Product_Release_Hardening"}
        if branch not in allowed_branches:
            errors.append(f"expected branch 7_Runtime_Foundation, 8_K_Phase, or 9_Product_Release_Hardening, got {branch}")

    return errors


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    errors = collect_errors(repo_root, require_ready=require_ready)
    return {
        "mode": "slides-runtime-phase-checkpoint",
        "phase": "RF2",
        "checkpoint": "RF2.0",
        "network_required": False,
        "runtime_changed_by_rf2_0": False,
        "dependency_versions_changed_by_rf2_0": False,
        "dockerfiles_changed_by_rf2_0": False,
        "llm_topology_changed_by_rf2_0": False,
        "browser_runtime_changed_by_rf2_0": False,
        "default_llm_provider": "local_gigachat",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "required_rf2_files": list(REQUIRED_RF2_FILES),
        "required_s_phase_surfaces": list(REQUIRED_S_PHASE_SURFACES),
        "required_rf1_handoff_surfaces": list(REQUIRED_RF1_HANDOFF_SURFACES),
        "next_recommended_step": "RF2.1 — Slides runtime capability inventory and baseline smoke",
        "next_phase_options": [
            "RF2 slides runtime continuation",
            "controlled dependency/security step without npm audit fix --force",
            "docs-only checkpoint before larger runtime work",
        ],
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KW Studio RF2 slides runtime phase checkpoint.")
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
