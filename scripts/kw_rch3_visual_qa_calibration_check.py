#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/RCH3_VISUAL_QA_HEURISTIC_CALIBRATION.md",
    "backend/app/services/k_phase/visual_qa.py",
    "scripts/kw_rch3_visual_qa_calibration_check.py",
    "backend/tests/smoke/test_rch3_visual_qa_calibration.py",
)
EXPECTED_BASE_AFTER_RCH2 = "08430e16f347938c61acf714180f5c37896ba5d7"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing RCH3 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready and run_git(repo_root, "branch", "--show-current") != "8_K_Phase":
        errors.append(f"expected branch 8_K_Phase, got {run_git(repo_root, 'branch', '--show-current')}")
    return errors


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.k_phase.renderer_quality import build_default_k3_quality_profile, improve_presentation_plan_render_quality
    from backend.app.services.k_phase.visual_qa import (
        VisualQAIssue,
        VisualQAPolicy,
        VisualQARuntimeRequest,
        _score_issues,
        _status_for,
        build_rch3_capabilities_report,
        run_visual_qa_runtime,
    )
    from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, render_approved_plan_to_pptx
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

    plan = PresentationPlan(
        deck_title="RCH3 visual QA calibration smoke",
        deck_goal="Verify calibrated visual QA heuristics without cloud services.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=2,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.ANALYSIS),
        slides=(
            PlannedSlide(
                slide_id="slide_001",
                slide_type=SlideType.TITLE,
                story_arc_stage=StoryArcStage.OPENING,
                title="Calibrated visual QA reduces noisy operator rework",
                bullets=(
                    "Minor overlap becomes information",
                    "Warnings remain explicit",
                    "Extreme overflow blocks approval",
                    "No raw slide text is stored",
                ),
                layout_hint="title_with_visual",
            ),
            PlannedSlide(
                slide_id="slide_002",
                slide_type=SlideType.CONTENT,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Heuristic calibration keeps release checks deterministic",
                bullets=("Local OOXML checks", "Safe issue counts", "Offline metadata"),
                layout_hint="content_with_visual",
            ),
        ),
    )
    quality = improve_presentation_plan_render_quality(plan, profile=build_default_k3_quality_profile(template_id="business_clean"))
    render = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=quality.render_plan,
            plan_snapshot_id="rch3_visual_qa_smoke_plan",
            render_mode="adaptive",
            template_id=quality.profile.template_id,
            artifact_filename="rch3-visual-qa-smoke.pptx",
        )
    )
    qa = run_visual_qa_runtime(
        VisualQARuntimeRequest(
            plan=quality.render_plan,
            artifact_content=render.artifact_content,
            plan_snapshot_id="rch3_visual_qa_smoke_plan",
            render_mode="adaptive",
            template_id=quality.profile.template_id,
            artifact_filename="rch3-visual-qa-smoke.pptx",
        )
    )
    policy = VisualQAPolicy()
    info_only = tuple(
        VisualQAIssue("rch3.info", "info", "slide_001", "minor", "inspect only")
        for _ in range(policy.max_info_count_to_pass)
    )
    warnings = tuple(
        VisualQAIssue("rch3.warning", "warning", "slide_001", "warning", "review")
        for _ in range(policy.max_warning_count_to_pass + 1)
    )
    blockers = (VisualQAIssue("rch3.blocker", "blocker", "slide_001", "blocker", "rework"),)
    capabilities = build_rch3_capabilities_report()
    metadata = qa.safe_metadata
    errors: list[str] = []

    if capabilities.get("rch3_visual_qa_heuristic_calibration_supported") is not True:
        errors.append("RCH3 calibration capability missing")
    if _status_for(score=_score_issues(info_only), issues=info_only, policy=policy) != "passed":
        errors.append("RCH3 info-only issues should not force operator review")
    if _status_for(score=_score_issues(warnings), issues=warnings, policy=policy) != "needs_operator_review":
        errors.append("RCH3 warning overflow should require operator review")
    if _status_for(score=_score_issues(blockers), issues=blockers, policy=policy) != "blocked":
        errors.append("RCH3 blocker issue should block approval")
    if qa.status not in {"passed", "needs_operator_review"}:
        errors.append(f"RCH3 smoke should not be blocked, got {qa.status}")
    if metadata.get("rch3_visual_qa_heuristic_calibration_supported") is not True:
        errors.append("RCH3 safe metadata missing calibration support")
    if metadata.get("calibrated_issue_counts", {}).get("warning") != metadata.get("warning_count"):
        errors.append("RCH3 calibrated warning count mismatch")
    if metadata.get("raw_slide_text_stored") is not False:
        errors.append("RCH3 safe metadata must not store raw slide text")
    if metadata.get("network_required") is not False:
        errors.append("RCH3 must remain offline/local")
    for key in (
        "api_endpoint_added_by_rch3",
        "db_schema_migration_added_by_rch3",
        "frontend_runtime_changed_by_rch3",
        "dependency_versions_changed_by_rch3",
        "dockerfiles_changed_by_rch3",
        "cloud_llm_added_by_rch3",
        "cloud_vision_added_by_rch3",
        "kimi_level_claimed_by_rch3",
    ):
        if capabilities.get(key) is not False:
            errors.append(f"RCH3 forbidden scope marker not false: {key}")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "rch3_visual_qa_heuristic_calibration_supported": capabilities.get("rch3_visual_qa_heuristic_calibration_supported") is True,
        "visual_qa_issue_severity_calibration_supported": capabilities.get("visual_qa_issue_severity_calibration_supported") is True,
        "visual_qa_false_positive_reduction_supported": capabilities.get("visual_qa_false_positive_reduction_supported") is True,
        "visual_qa_false_negative_guard_supported": capabilities.get("visual_qa_false_negative_guard_supported") is True,
        "visual_qa_info_warning_blocker_split_supported": capabilities.get("visual_qa_info_warning_blocker_split_supported") is True,
        "visual_qa_status": qa.status,
        "visual_qa_score": qa.score,
        "issue_count": metadata.get("issue_count"),
        "info_count": metadata.get("info_count"),
        "warning_count": metadata.get("warning_count"),
        "blocker_count": metadata.get("blocker_count"),
        "api_endpoint_added_by_rch3": False,
        "db_schema_migration_added_by_rch3": False,
        "frontend_runtime_changed_by_rch3": False,
        "dependency_versions_changed_by_rch3": False,
        "dockerfiles_changed_by_rch3": False,
        "cloud_llm_added_by_rch3": False,
        "cloud_vision_added_by_rch3": False,
        "kimi_level_claimed_by_rch3": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = static_errors + list(smoke.get("errors", []))
    return {
        "mode": "rch3-visual-qa-heuristic-calibration",
        "phase": "release-candidate-hardening",
        "checkpoint": "RCH3",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_rch2": EXPECTED_BASE_AFTER_RCH2,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        **{key: value for key, value in smoke.items() if key not in {"status", "errors"}},
        "next_recommended_step": "RC4 — release candidate artifact pack",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RCH3 visual QA heuristic calibration check.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"RCH3 visual QA calibration: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
