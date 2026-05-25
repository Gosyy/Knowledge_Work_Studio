#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/P9_4_VISUAL_QA_SEMANTIC_GUARD.md",
    "docs/codex/P9_PRODUCT_RELEASE_HARDENING_PLAN.md",
    "backend/app/services/k_phase/visual_qa.py",
    "scripts/kw_p9_4_visual_qa_semantic_guard_check.py",
    "backend/tests/smoke/test_p9_4_visual_qa_semantic_guard.py",
)
EXPECTED_BASE_AFTER_P9_3 = "1f546bb46de3f11f1a0a12f185bdcb1800632b18"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P9-4 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready and run_git(repo_root, "branch", "--show-current") != "9_Product_Release_Hardening":
        errors.append(f"expected branch 9_Product_Release_Hardening, got {run_git(repo_root, 'branch', '--show-current')}")
    return errors


def _build_bad_plan():
    from backend.app.services.slides_service.blocks import ComparisonBlock, TableBlock
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

    return PresentationPlan(
        deck_title="P9-4 visual QA semantic guard smoke",
        deck_goal="Validate product-quality guard for visually clean but semantically weak artifacts.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=2,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.ANALYSIS),
        slides=(
            PlannedSlide(
                slide_id="slide_001",
                slide_type=SlideType.TITLE,
                story_arc_stage=StoryArcStage.OPENING,
                title="K1 Plan: Option,Strength,Weakness,Recommendation",
                bullets=("Additional source-grounded planning point 1", "Decision table appears as raw CSV header"),
                layout_hint="title_with_visual",
            ),
            PlannedSlide(
                slide_id="slide_002",
                slide_type=SlideType.COMPARISON,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Decision comparison needs operator review",
                bullets=("Direct local GigaChat default", "Optional LiteLLM gateway", "Local-model fallback is out of runtime scope"),
                layout_hint="two_column_comparison",
                blocks=(
                    ComparisonBlock(
                        block_id="slide_002_current_target",
                        left_title="Current / Option A",
                        left_items=("Direct local GigaChat",),
                        right_title="Target / Option B",
                        right_items=("Recommended next step",),
                    ),
                    TableBlock(
                        block_id="slide_002_review_table",
                        columns=("Signal", "Evidence", "Review"),
                        rows=(("S1", "Option,Strength,Weakness,Recommendation", "review"),),
                        caption="Generic review placeholder",
                    ),
                ),
            ),
        ),
    )


def _build_good_plan():
    from backend.app.services.slides_service.blocks import ComparisonBlock, TableBlock
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

    return PresentationPlan(
        deck_title="P9-4 semantic guard clean smoke",
        deck_goal="Validate visual QA can still pass source-specific product-quality content.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=2,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.RECOMMENDATION),
        slides=(
            PlannedSlide(
                slide_id="slide_001",
                slide_type=SlideType.TITLE,
                story_arc_stage=StoryArcStage.OPENING,
                title="Offline release decision for local GigaChat topology",
                bullets=("Default runtime stays on Server 3", "Server 2 remains optional gateway and heavy runtime node"),
                layout_hint="title_with_visual",
            ),
            PlannedSlide(
                slide_id="slide_002",
                slide_type=SlideType.COMPARISON,
                story_arc_stage=StoryArcStage.RECOMMENDATION,
                title="Decision matrix preserves runtime option trade-offs",
                bullets=("Direct local GigaChat is the recommended default", "LiteLLM gateway stays optional", "Local-model fallback remains out of runtime scope"),
                layout_hint="two_column_comparison",
                blocks=(
                    ComparisonBlock(
                        block_id="slide_002_runtime_options",
                        left_title="Runtime options",
                        left_items=("Direct local GigaChat", "Optional LiteLLM gateway"),
                        right_title="Decision criteria",
                        right_items=("Offline default", "No hidden public internet dependency"),
                    ),
                    TableBlock(
                        block_id="slide_002_decision_table",
                        columns=("Option", "Strength", "Weakness", "Recommendation"),
                        rows=(("Direct GigaChat", "Offline default", "Requires local endpoint", "Use by default"),),
                        caption="Decision matrix",
                    ),
                ),
            ),
        ),
    )


def _render_and_qa(plan, *, filename: str):
    from backend.app.services.k_phase.visual_qa import VisualQARuntimeRequest, run_visual_qa_runtime
    from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, render_approved_plan_to_pptx

    render = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=plan,
            plan_snapshot_id=filename.removesuffix(".pptx"),
            render_mode="adaptive",
            template_id="business_clean",
            artifact_filename=filename,
        )
    )
    return run_visual_qa_runtime(
        VisualQARuntimeRequest(
            plan=plan,
            artifact_content=render.artifact_content,
            plan_snapshot_id=filename.removesuffix(".pptx"),
            render_mode="adaptive",
            template_id="business_clean",
            artifact_filename=filename,
        )
    )


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.k_phase.visual_qa import _has_raw_csv_rendering_signature, build_p9_4_capabilities_report

    bad = _render_and_qa(_build_bad_plan(), filename="p9-4-bad-smoke.pptx")
    good = _render_and_qa(_build_good_plan(), filename="p9-4-good-smoke.pptx")
    capabilities = build_p9_4_capabilities_report()
    errors: list[str] = []

    bad_checks = {issue.check_id for issue in bad.issues}
    semantic_issues = tuple(issue for issue in bad.issues if issue.check_id.startswith("p9_4."))
    natural_decision_language = "compare each option by strength, weakness, and recommendation"
    if bad.status != "blocked":
        errors.append(f"P9-4 bad semantic smoke should be blocked, got {bad.status}")
    if not semantic_issues or any(getattr(issue, "issue_id", None) != issue.check_id for issue in semantic_issues):
        errors.append("P9-4 semantic issues must expose issue_id for K6 operator gate compatibility")
    if _has_raw_csv_rendering_signature(natural_decision_language):
        errors.append("P9-4 raw CSV guard must not flag natural decision-matrix language")
    for check_id in ("p9_4.generic_fallback_label", "p9_4.raw_csv_rendering"):
        if check_id not in bad_checks:
            errors.append(f"missing expected semantic blocker: {check_id}")
    if "p9_4.arbitrary_current_target_layout" not in bad_checks:
        errors.append("missing arbitrary Current/Target semantic warning")
    if "p9_4.generic_table_review_placeholder" not in bad_checks:
        errors.append("missing generic table review placeholder warning")
    if bad.safe_metadata.get("semantic_review_guard_blocker_count", 0) < 2:
        errors.append("semantic blocker count should include fallback label and raw CSV rendering")
    if good.safe_metadata.get("semantic_review_guard_issue_count") != 0:
        errors.append("clean decision-matrix smoke should not produce P9-4 semantic issues")
    if good.status not in {"passed", "needs_operator_review"}:
        errors.append(f"clean semantic smoke should not be blocked, got {good.status}")
    for key, expected in (
        ("p9_4_visual_qa_semantic_guard_supported", True),
        ("visual_qa_product_quality_guard_supported", True),
        ("visual_qa_semantic_issue_detection_supported", True),
        ("visual_qa_human_review_alignment_supported", True),
        ("visual_qa_issue_id_compatibility_supported", True),
        ("visual_qa_raw_csv_false_positive_guard_supported", True),
        ("network_required_by_p9_4", False),
        ("api_endpoint_added_by_p9_4", False),
        ("db_schema_migration_added_by_p9_4", False),
        ("frontend_runtime_changed_by_p9_4", False),
        ("dependency_versions_changed_by_p9_4", False),
        ("dockerfiles_changed_by_p9_4", False),
        ("cloud_llm_added_by_p9_4", False),
        ("cloud_vision_added_by_p9_4", False),
        ("kimi_level_claimed_by_p9_4", False),
    ):
        if capabilities.get(key) is not expected:
            errors.append(f"P9-4 capability mismatch for {key}")
    if bad.safe_metadata.get("raw_slide_text_stored") is not False:
        errors.append("P9-4 must not store raw slide text")
    if bad.safe_metadata.get("network_required") is not False:
        errors.append("P9-4 must remain offline/local")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "p9_4_visual_qa_semantic_guard_supported": capabilities.get("p9_4_visual_qa_semantic_guard_supported") is True,
        "visual_qa_product_quality_guard_supported": capabilities.get("visual_qa_product_quality_guard_supported") is True,
        "visual_qa_semantic_issue_detection_supported": capabilities.get("visual_qa_semantic_issue_detection_supported") is True,
        "visual_qa_human_review_alignment_supported": capabilities.get("visual_qa_human_review_alignment_supported") is True,
        "bad_semantic_status": bad.status,
        "bad_semantic_score": bad.score,
        "bad_semantic_issue_count": bad.safe_metadata.get("semantic_review_guard_issue_count"),
        "bad_semantic_warning_count": bad.safe_metadata.get("semantic_review_guard_warning_count"),
        "bad_semantic_blocker_count": bad.safe_metadata.get("semantic_review_guard_blocker_count"),
        "good_semantic_status": good.status,
        "good_semantic_issue_count": good.safe_metadata.get("semantic_review_guard_issue_count"),
        "api_endpoint_added_by_p9_4": False,
        "db_schema_migration_added_by_p9_4": False,
        "frontend_runtime_changed_by_p9_4": False,
        "dependency_versions_changed_by_p9_4": False,
        "dockerfiles_changed_by_p9_4": False,
        "cloud_llm_added_by_p9_4": False,
        "cloud_vision_added_by_p9_4": False,
        "kimi_level_claimed_by_p9_4": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = static_errors + list(smoke.get("errors", []))
    return {
        "mode": "p9-4-visual-qa-semantic-guard",
        "phase": "P9 Product Release Hardening",
        "checkpoint": "P9-4",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p9_3": EXPECTED_BASE_AFTER_P9_3,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        **{key: value for key, value in smoke.items() if key not in {"status", "errors"}},
        "next_recommended_step": "Run targeted pytest, production readiness checks-only, then full runner and Docker smoke after commit.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P9-4 visual QA semantic guard check.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"P9-4 visual QA semantic guard: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
