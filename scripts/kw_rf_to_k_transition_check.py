#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "docs/codex/K_PHASE_PRODUCT_POWER_PLAN.md",
    "docs/codex/RF_EXIT_TO_K_PHASE_CRITERIA.md",
    "docs/codex/RUNTIME_FOUNDATION_PHASE_PLAN.md",
    "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md",
    "scripts/kw_rf_to_k_transition_check.py",
    "backend/tests/smoke/test_rf2_2a_rf_to_k_transition.py",
)

REQUIRED_PHRASES = {
    "k_plan": (
        "docs/codex/K_PHASE_PRODUCT_POWER_PLAN.md",
        (
            "Kimi-level does not mean a single stronger PPTX generator",
            "source intake -> document understanding -> local/offline GigaChat planning",
            "K0 — Kimi-level rubric and golden deck benchmark",
            "K6 — End-to-end Kimi-like workflow",
            "direct local GigaChat-first",
            "Do not run `npm audit fix --force`",
            "RF must finish before K-phase starts",
        ),
    ),
    "rf_exit": (
        "docs/codex/RF_EXIT_TO_K_PHASE_CRITERIA.md",
        (
            "The project must finish RF before entering K-phase product-power work",
            "RF is not expected to reach Kimi-level slides quality",
            "RF2.3 plan snapshot persistence and task event stream runtime wiring",
            "RF3 — Real document ingestion foundation",
            "RF4 — Local GigaChat integration hardening",
            "RF must not absorb K-phase",
            "K-readiness matrix",
        ),
    ),
    "runtime_foundation": (
        "docs/codex/RUNTIME_FOUNDATION_PHASE_PLAN.md",
        (
            "RF2.2a — RF-to-K transition guard and Kimi-level Product Power roadmap",
            "K-phase is the product-power phase",
            "finish RF0-RF4 before K-phase",
            "K_PHASE_PRODUCT_POWER_PLAN.md",
            "RF_EXIT_TO_K_PHASE_CRITERIA.md",
        ),
    ),
    "slides_phase": (
        "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md",
        (
            "RF2.2a — RF-to-K transition guard and Kimi-level Product Power roadmap",
            "RF2.3 remains the next runtime implementation step",
            "Kimi-level is deferred to K-phase",
            "RF2 must not absorb open-ended K-phase product-power work",
        ),
    ),
}


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


def read_text(repo_root: Path, rel: str) -> str:
    return (repo_root / rel).read_text(encoding="utf-8")


def collect_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing RF2.2a required file: {rel}")

    for group, (rel, phrases) in REQUIRED_PHRASES.items():
        path = repo_root / rel
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in content:
                errors.append(f"missing RF2.2a phrase in {group}: {phrase}")

    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        allowed_branches = {"7_Runtime_Foundation", "8_K_Phase"}
        if branch not in allowed_branches:
            errors.append(f"expected branch 7_Runtime_Foundation or 8_K_Phase, got {branch}")

    return errors


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    errors = collect_errors(repo_root, require_ready=require_ready)

    return {
        "mode": "rf-to-k-transition-guard",
        "phase": "RF2",
        "checkpoint": "RF2.2a",
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "network_required": False,
        "runtime_changed_by_rf2_2a": False,
        "dependency_versions_changed_by_rf2_2a": False,
        "dockerfiles_changed_by_rf2_2a": False,
        "frontend_runtime_changed_by_rf2_2a": False,
        "llm_topology_changed_by_rf2_2a": False,
        "browser_runtime_changed_by_rf2_2a": False,
        "default_route": [
            "finish_RF0_RF4",
            "run_RF_closure",
            "enter_K_phase_only_after_RF_exit_criteria",
            "use_K_phase_for_Kimi_level_product_power",
        ],
        "accepted_sequence_from_current_state": [
            "RF2.2a",
            "RF2.3",
            "RF2.4",
            "RF2.5",
            "RF2.6",
            "RF2.7",
            "RF2_closure",
            "RF3",
            "RF4",
            "RF_closure",
            "K0",
        ],
        "k_phase_target": "whole_slides_product_loop_not_generator_only",
        "kimi_level_supported_now": False,
        "rf_must_finish_before_k_phase": True,
        "rf_must_not_absorb_open_ended_k_phase_work": True,
        "new_chat_prompt_must_include_plan": True,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RF2.2a RF-to-K transition guard check.")
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
