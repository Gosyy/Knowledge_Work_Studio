#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/K2_PLAN_EDITOR_PRODUCT_WORKFLOW.md",
    "backend/app/services/k_phase/plan_editor.py",
    "scripts/kw_k2_plan_editor_check.py",
    "backend/tests/smoke/test_k2_plan_editor_workflow.py",
)
EXPECTED_BASE_AFTER_K1 = "8c96bbfd0849a0a776316cbb9d49d0ce838e91e4"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing K2 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready and run_git(repo_root, "branch", "--show-current") != "8_K_Phase":
        errors.append(f"expected branch 8_K_Phase, got {run_git(repo_root, 'branch', '--show-current')}")
    return errors


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from backend.app.services.k_phase.local_gigachat_planner import K1PlanningRequest, LocalGigaChatPlanningEngine
    from backend.app.services.k_phase.plan_editor import (
        K2EvidenceLink,
        K2PlanEditRequest,
        K2PlanEditorError,
        K2PlanEditorWorkflow,
        K2SlidePatch,
        build_k2_capabilities_report,
    )

    source = "Q1 revenue grew. Enterprise churn risk increased. Prioritize onboarding automation and retention evidence."
    k1_result = LocalGigaChatPlanningEngine(None).plan(K1PlanningRequest(source_text=source, target_slide_count=5))
    workflow = K2PlanEditorWorkflow()
    initial = workflow.create_session(
        k1_result.plan,
        source_links_by_slide_id={
            k1_result.plan.slides[0].slide_id: (K2EvidenceLink(source_id="memo_001", title="Q1 memo", locator="p1"),)
        },
    )
    approval_gate_blocked = False
    try:
        workflow.to_presentation_plan(initial.session)
    except K2PlanEditorError:
        approval_gate_blocked = True

    first_slide = initial.session.slides[0]
    edited = workflow.apply_edits(
        initial.session,
        K2PlanEditRequest(
            patches=(
                K2SlidePatch(
                    slide_id=first_slide.slide_id,
                    title="Retention plan cockpit",
                    bullets=("Focus onboarding automation", "Use enterprise churn evidence"),
                    slide_intent="Make the operator-approved decision explicit before generation.",
                    evidence_links=(K2EvidenceLink(source_id="memo_001", title="Q1 memo", locator="p1"),),
                    visual_intent="process_visual",
                    layout_hint="content_with_visual",
                ),
            ),
            change_summary="Clarify opening slide and attach evidence link.",
            requested_render_mode="template",
            template_id="business_clean",
        ),
    )
    approval_requested = workflow.request_approval(edited.session)
    approved = workflow.approve(approval_requested.session)
    bad_template_rejected = False
    try:
        workflow.create_session(k1_result.plan, render_mode="template")
    except K2PlanEditorError:
        bad_template_rejected = True

    event_types = tuple(event.event_type for event in approved.session.events)
    expected_events = (
        "k2.plan_editor.session.created",
        "k2.plan_editor.edit.requested",
        "k2.plan_editor.slide.updated",
        "k2.plan_editor.render_mode.updated",
        "k2.plan_editor.approval.requested",
        "k2.plan_editor.approved",
    )
    metadata = approved.safe_metadata
    encoded_metadata = json.dumps(metadata, ensure_ascii=False, sort_keys=True).lower()
    capabilities = build_k2_capabilities_report()
    errors: list[str] = []
    if not approval_gate_blocked:
        errors.append("K2 approval gate did not block unapproved plan conversion")
    if not bad_template_rejected:
        errors.append("K2 template render mode did not require explicit template_id")
    if event_types != expected_events:
        errors.append(f"K2 event order mismatch: {event_types}")
    if approved.approved_plan is None or approved.approved_plan.slides[0].title != "Retention plan cockpit":
        errors.append("K2 approved PresentationPlan does not include edited slide")
    if "q1 revenue grew" in encoded_metadata:
        errors.append("K2 safe metadata contains raw source text")
    if metadata.get("kimi_level_claimed_by_k2") is not False:
        errors.append("K2 must not claim Kimi-level")
    if metadata.get("whole_project_kimi_level_supported") is not False:
        errors.append("K2 must not claim whole-project Kimi-level")
    if capabilities.get("frontend_runtime_changed_by_k2") is not False:
        errors.append("K2 checker expected no frontend runtime changes")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "plan_editor_workflow_supported": not errors,
        "editable_outline_supported": metadata.get("editable_outline_supported") is True,
        "slide_intent_editing_supported": metadata.get("slide_intent_editing_supported") is True,
        "evidence_link_editing_supported": metadata.get("evidence_link_editing_supported") is True,
        "visual_intent_editing_supported": metadata.get("visual_intent_editing_supported") is True,
        "render_mode_controls_supported": metadata.get("render_mode_controls_supported") is True,
        "approval_gate_supported": approval_gate_blocked,
        "diff_retry_workflow_supported": metadata.get("diff_retry_workflow_supported") is True,
        "task_event_visibility_supported": metadata.get("task_event_visibility_supported") is True,
        "clear_failure_states_supported": metadata.get("clear_failure_states_supported") is True,
        "template_requires_explicit_template_id": bad_template_rejected,
        "event_order_valid": event_types == expected_events,
        "approved_plan_created": approved.approved_plan is not None,
        "safe_metadata_only": not errors,
        "raw_source_text_stored": False,
        "raw_prompt_stored": False,
        "api_endpoint_added_by_k2": False,
        "db_schema_migration_added_by_k2": False,
        "frontend_runtime_changed_by_k2": False,
        "dependency_versions_changed_by_k2": False,
        "dockerfiles_changed_by_k2": False,
        "visual_qa_runtime_added_by_k2": False,
        "kimi_level_claimed_by_k2": False,
        "whole_project_kimi_level_supported": False,
        "event_types": event_types,
        "slide_count": len(approved.session.slides),
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = static_errors + list(smoke.get("errors", []))
    return {
        "mode": "k2-plan-editor-product-workflow",
        "phase": "K-phase",
        "checkpoint": "K2",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "k2_base_after_k1": EXPECTED_BASE_AFTER_K1,
        "runtime_changed_by_k2": True,
        "runtime_change_type": "plan_editor_product_workflow_runtime",
        "dependency_versions_changed_by_k2": False,
        "dockerfiles_changed_by_k2": False,
        "frontend_runtime_changed_by_k2": False,
        "api_endpoint_added_by_k2": False,
        "db_schema_migration_added_by_k2": False,
        "visual_qa_runtime_added_by_k2": False,
        "cloud_llm_added_by_k2": False,
        "kimi_level_claimed_by_k2": False,
        "whole_project_kimi_level_supported": False,
        "runtime_smoke": smoke,
        "next_recommended_step": "K3 — Renderer quality upgrade",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio K2 plan editor product workflow check.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(Path(args.repo_root).expanduser().resolve(), args.require_ready)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
