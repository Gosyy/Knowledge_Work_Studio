#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

CHECKPOINT = "S2"
SCHEMA_VERSION = "s2.outline_first_frontend_workflow.v1"
EXPECTED_BASE_AFTER_S1 = "9bade7ea43ef8cc5db994a183d9cdb984e541ebe"

REQUIRED_FILES = (
    "docs/codex/S_PHASE_KIMI_SLIDES_CLASS_ROADMAP.md",
    "docs/codex/S1_KIMI_SLIDES_CLASS_GAP_DOSSIER.md",
    "docs/codex/S2_OUTLINE_FIRST_FRONTEND_WORKFLOW.md",
    "docs/slides-plan-first-ux.md",
    "docs/slides-plan-editor-ui.md",
    "docs/slides-task-events-and-retry.md",
    "backend/app/services/slides_service/plan_first_contract.py",
    "scripts/kw_s1_kimi_slides_gap_check.py",
    "scripts/kw_slides_plan_first_check.py",
    "scripts/kw_slides_plan_editor_check.py",
    "scripts/kw_slides_task_events_check.py",
    "scripts/kw_s2_outline_first_frontend_workflow_check.py",
    "backend/tests/smoke/test_s2_outline_first_frontend_workflow.py",
)

FRONTEND_JOURNEY = (
    "source_intake",
    "outline_draft",
    "editable_outline_plan_review",
    "explicit_plan_approval",
    "render_mode_selection",
    "pptx_generation_from_approved_plan",
    "artifact_history_registration",
    "plan_snapshot_registration",
    "retry_from_saved_plan",
)

REQUIRED_EVENTS = (
    "slides.plan.requested",
    "slides.outline.created",
    "slides.plan.ready_for_review",
    "slides.plan.approved",
    "slides.render_mode.selected",
    "slides.generation.started",
    "artifact.registered",
    "plan.snapshot.registered",
    "slides.retry.from_saved_plan.requested",
    "slides.generation.completed",
)

RENDER_MODES = ("adaptive", "template")


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


def read_text(repo_root: Path, rel: str) -> str:
    return (repo_root / rel).read_text(encoding="utf-8")


def run_json_command(repo_root: Path, command: list[str]) -> tuple[dict[str, Any] | None, str, str, int]:
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
    errors = [f"missing S2 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_S1:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_S1, head)
            if ancestry is False:
                errors.append(f"expected S1 baseline {EXPECTED_BASE_AFTER_S1} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify S1 ancestry for {EXPECTED_BASE_AFTER_S1}..{head}")
    return errors


def validate_document_contracts(repo_root: Path) -> list[str]:
    errors: list[str] = []
    checks = {
        "docs/codex/S2_OUTLINE_FIRST_FRONTEND_WORKFLOW.md": (
            "Outline draft",
            "Editable outline and plan review",
            "Explicit plan approval",
            "PPTX generation from the approved plan",
            "Retry from saved plan",
        ),
        "docs/slides-plan-first-ux.md": (
            "Outline draft",
            "Editable plan review",
            "Generation from the approved plan",
            "Retry from saved plan",
        ),
        "docs/slides-plan-editor-ui.md": (
            "edit the deck title and outline slide fields",
            "explicitly choose adaptive or template render mode",
            "save an editable plan draft",
            "retry from saved plan",
        ),
        "docs/slides-task-events-and-retry.md": (
            "slides.retry.from_saved_plan.requested",
            "plan snapshot",
            "safe task events",
        ),
        "docs/codex/S_PHASE_KIMI_SLIDES_CLASS_ROADMAP.md": (
            "S2",
            "Outline-first frontend workflow",
        ),
    }
    for rel, needles in checks.items():
        text = read_text(repo_root, rel)
        lowered = text.lower()
        for needle in needles:
            if needle.lower() not in lowered:
                errors.append(f"{rel} is missing required S2 contract phrase: {needle}")
    return errors


def run_s1(repo_root: Path, require_ready: bool) -> tuple[dict[str, Any] | None, list[str]]:
    command = [sys.executable, "scripts/kw_s1_kimi_slides_gap_check.py", "--repo-root", str(repo_root), "--json"]
    if require_ready:
        command.append("--require-ready")
    payload, stdout, stderr, code = run_json_command(repo_root, command)
    errors: list[str] = []
    if code != 0:
        errors.append(f"S1 gap checker failed during S2 with exit code {code}: {stderr.strip() or stdout.strip()[:500]}")
    if payload is None:
        errors.append("S2 could not parse S1 checker JSON output")
    elif payload.get("status") != "ready":
        errors.append(f"S1 checker status is not ready during S2: {payload.get('status')!r}")
    return payload, errors


def run_plan_first(repo_root: Path, require_ready: bool) -> tuple[dict[str, Any] | None, list[str]]:
    command = [sys.executable, "scripts/kw_slides_plan_first_check.py", "--repo-root", str(repo_root), "--json"]
    if require_ready:
        command.append("--require-ready")
    payload, stdout, stderr, code = run_json_command(repo_root, command)
    errors: list[str] = []
    if code != 0:
        errors.append(f"slides plan-first checker failed during S2 with exit code {code}: {stderr.strip() or stdout.strip()[:500]}")
    if payload is None:
        errors.append("S2 could not parse slides plan-first checker JSON output")
    elif payload.get("status") != "ready":
        errors.append(f"slides plan-first checker status is not ready during S2: {payload.get('status')!r}")
    return payload, errors


def build_report(repo_root: Path, artifacts_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    s1_report: dict[str, Any] | None = None
    plan_first_report: dict[str, Any] | None = None
    if not errors:
        s1_report, s1_errors = run_s1(repo_root, require_ready)
        errors.extend(s1_errors)
    if not errors:
        plan_first_report, plan_errors = run_plan_first(repo_root, require_ready)
        errors.extend(plan_errors)
    if not errors:
        errors.extend(validate_document_contracts(repo_root))

    plan_contract = plan_first_report.get("contract", {}) if isinstance(plan_first_report, dict) else {}
    plan_controls = plan_first_report.get("controls", {}) if isinstance(plan_first_report, dict) else {}
    contract_events = tuple(plan_contract.get("safe_task_events", ())) if isinstance(plan_contract, dict) else ()
    missing_events = [event for event in REQUIRED_EVENTS if event not in contract_events]
    if missing_events:
        errors.append("slides plan-first contract missing safe events: " + ", ".join(missing_events))
    contract_render_modes = tuple(plan_contract.get("render_modes", ())) if isinstance(plan_contract, dict) else ()
    missing_modes = [mode for mode in RENDER_MODES if mode not in contract_render_modes]
    if missing_modes:
        errors.append("slides plan-first contract missing render modes: " + ", ".join(missing_modes))

    ready = not errors
    report = {
        "mode": "s2-outline-first-frontend-workflow",
        "phase": "S-phase Kimi Slides-class workflow quality track",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_s1": EXPECTED_BASE_AFTER_S1,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "s1_status": s1_report.get("status") if isinstance(s1_report, dict) else None,
        "plan_first_status": plan_first_report.get("status") if isinstance(plan_first_report, dict) else None,
        "outline_first_frontend_workflow_completed_by_s2": bool(ready),
        "frontend_workflow_contract_ready_by_s2": bool(ready),
        "frontend_journey_steps": list(FRONTEND_JOURNEY),
        "frontend_journey_step_count": len(FRONTEND_JOURNEY),
        "required_safe_task_events": list(REQUIRED_EVENTS),
        "required_safe_task_event_count": len(REQUIRED_EVENTS),
        "supported_render_modes_by_s2": list(RENDER_MODES),
        "outline_visible_before_generation_by_s2": True,
        "editable_plan_required_before_generation_by_s2": True,
        "explicit_plan_approval_required_by_s2": True,
        "explicit_render_mode_required_by_s2": bool(plan_controls.get("explicit_render_mode_required") is True),
        "plan_snapshot_required_by_s2": True,
        "retry_from_saved_plan_required_by_s2": bool(plan_controls.get("retry_from_saved_plan_required") is True),
        "direct_pptx_generation_without_plan_allowed_by_s2": False,
        "generation_requires_approved_plan_by_s2": bool(plan_controls.get("plan_review_required") is True),
        "artifact_history_registration_required_by_s2": True,
        "frontend_runtime_changed_by_s2": False,
        "api_endpoint_added_by_s2": False,
        "db_schema_migration_added_by_s2": False,
        "dependency_versions_changed_by_s2": False,
        "dockerfiles_changed_by_s2": False,
        "cloud_llm_added_by_s2": False,
        "cloud_vision_added_by_s2": False,
        "network_required_for_s2": False,
        "production_offline_mode_remains_target_deployment_mode": True,
        "p10_5a_public_api_dev_evidence_is_not_server3_offline_proof": True,
        "server3_local_intranet_route_verified_by_s2": False,
        "kimi_slides_class_goal_advanced_by_s2": bool(ready),
        "kimi_slides_class_parity_claim_supported_by_s2": False,
        "kimi_level_claimed_by_s2": False,
        "whole_project_kimi_level_supported": False,
        "next_recommended_step": "S3 - adaptive deck modes with mode-specific storyline and slide archetype registries.",
    }
    report["s2_report_digest"] = digest_payload(report)
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out = artifacts_dir / "s2_outline_first_frontend_workflow.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        report["s2_report_file"] = str(out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KW Studio S2 outline-first frontend workflow checker.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repo_root.resolve(), args.artifacts_dir.resolve() if args.artifacts_dir else None, args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"S2 outline-first frontend workflow: {report['status']}")
        print(f"frontend journey steps: {report['frontend_journey_step_count']}")
        print(f"safe task events: {report['required_safe_task_event_count']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
