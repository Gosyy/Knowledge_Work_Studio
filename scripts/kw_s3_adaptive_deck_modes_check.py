#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.adaptive_deck_modes import adaptive_deck_modes_report  # noqa: E402

CHECKPOINT = "S3"
SCHEMA_VERSION = "s3.adaptive_deck_modes.v1"
EXPECTED_BASE_AFTER_S2 = "fb5d888f9348c07a57b94387f0b201f38c785010"

REQUIRED_FILES = (
    "docs/codex/S_PHASE_KIMI_SLIDES_CLASS_ROADMAP.md",
    "docs/codex/S1_KIMI_SLIDES_CLASS_GAP_DOSSIER.md",
    "docs/codex/S2_OUTLINE_FIRST_FRONTEND_WORKFLOW.md",
    "docs/codex/S3_ADAPTIVE_DECK_MODES.md",
    "docs/slides-plan-first-ux.md",
    "docs/slides-task-events-and-retry.md",
    "backend/app/services/slides_service/plan_first_contract.py",
    "backend/app/services/slides_service/render_mode_contract.py",
    "backend/app/services/slides_service/render_mode_runtime.py",
    "backend/app/services/slides_service/adaptive_deck_modes.py",
    "scripts/kw_s1_kimi_slides_gap_check.py",
    "scripts/kw_s2_outline_first_frontend_workflow_check.py",
    "scripts/kw_s3_adaptive_deck_modes_check.py",
    "backend/tests/smoke/test_s3_adaptive_deck_modes.py",
)


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def digest_payload(payload: Any) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def run_checker(repo_root: Path, script: str, require_ready: bool) -> tuple[dict[str, Any] | None, str, str, int]:
    command = [sys.executable, script, "--repo-root", str(repo_root), "--json"]
    if require_ready:
        command.append("--require-ready")
    result = subprocess.run(command, cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    payload: dict[str, Any] | None = None
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = None
    return payload, result.stdout, result.stderr, result.returncode


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing S3 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_S2:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_S2, head)
            if ancestry is False:
                errors.append(f"expected S2 baseline {EXPECTED_BASE_AFTER_S2} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify S2 ancestry for {EXPECTED_BASE_AFTER_S2}..{head}")
    return errors


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    s1_payload: dict[str, Any] | None = None
    s2_payload: dict[str, Any] | None = None
    if not errors:
        s1_payload, stdout, stderr, returncode = run_checker(repo_root, "scripts/kw_s1_kimi_slides_gap_check.py", require_ready)
        if returncode != 0:
            errors.append(f"S1 checker failed during S3 with exit code {returncode}: {stderr.strip() or stdout.strip()[:500]}")
        elif not s1_payload or s1_payload.get("status") != "ready":
            errors.append("S1 checker did not report ready during S3")
    if not errors:
        s2_payload, stdout, stderr, returncode = run_checker(repo_root, "scripts/kw_s2_outline_first_frontend_workflow_check.py", require_ready)
        if returncode != 0:
            errors.append(f"S2 checker failed during S3 with exit code {returncode}: {stderr.strip() or stdout.strip()[:500]}")
        elif not s2_payload or s2_payload.get("status") != "ready":
            errors.append("S2 checker did not report ready during S3")
    registry_report = adaptive_deck_modes_report()
    errors.extend(registry_report.get("errors", []))
    ready = not errors
    report = {
        "mode": "s3-adaptive-deck-modes",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_s2": EXPECTED_BASE_AFTER_S2,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "s1_report_digest": digest_payload(s1_payload) if s1_payload else None,
        "s2_report_digest": digest_payload(s2_payload) if s2_payload else None,
        "adaptive_deck_modes_report_digest": digest_payload(registry_report),
        "adaptive_deck_modes_completed_by_s3": bool(ready),
        "adaptive_deck_mode_count": registry_report.get("adaptive_deck_mode_count"),
        "expected_adaptive_deck_mode_count": registry_report.get("expected_adaptive_deck_mode_count"),
        "adaptive_deck_mode_ids": registry_report.get("adaptive_deck_mode_ids"),
        "mode_specific_storyline_required_by_s3": registry_report.get("mode_specific_storyline_required_by_s3"),
        "slide_archetype_registry_ready_by_s3": registry_report.get("slide_archetype_registry_ready_by_s3"),
        "table_chart_policy_ready_for_s4": registry_report.get("table_chart_policy_ready_for_s4"),
        "visual_qa_expectations_ready_for_s9": registry_report.get("visual_qa_expectations_ready_for_s9"),
        "source_to_slide_provenance_required_by_s3": registry_report.get("source_to_slide_provenance_required_by_s3"),
        "offline_ready_by_s3": registry_report.get("offline_ready_by_s3"),
        "public_internet_required_by_s3": False,
        "browser_runtime_required_by_s3": False,
        "api_endpoint_added_by_s3": False,
        "db_schema_migration_added_by_s3": False,
        "frontend_runtime_changed_by_s3": False,
        "dependency_versions_changed_by_s3": False,
        "dockerfiles_changed_by_s3": False,
        "cloud_llm_added_by_s3": False,
        "cloud_vision_added_by_s3": False,
        "kimi_level_claimed_by_s3": False,
        "whole_project_kimi_level_supported": False,
        "server3_local_intranet_route_verified_by_s3": False,
        "next_recommended_step": "S4 - native table/chart/diagram rendering from mode-specific archetypes.",
    }
    report["s3_report_digest"] = digest_payload(report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KW Studio S3 adaptive deck modes checker.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repo_root.resolve(), args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"S3 adaptive deck modes: {report['status']}")
        print(f"adaptive deck modes: {report['adaptive_deck_mode_count']}/{report['expected_adaptive_deck_mode_count']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
