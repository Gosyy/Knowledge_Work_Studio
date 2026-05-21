from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_rch3_visual_qa_calibration_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def calibration_plan() -> PresentationPlan:
    bullets = (
        "Visual QA should distinguish minor information from warnings and blockers",
        "RCH3 calibrates overlap and overflow thresholds for operator review",
        "Safe metadata keeps counts and status without storing raw slide text",
        "Offline runtime remains local and deterministic",
    )
    return PresentationPlan(
        deck_title="RCH3 visual QA calibration",
        deck_goal="Validate calibrated visual QA severity and metadata.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=2,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.ANALYSIS),
        slides=(
            PlannedSlide(
                slide_id="slide_001",
                slide_type=SlideType.TITLE,
                story_arc_stage=StoryArcStage.OPENING,
                title="Calibrated visual QA separates info warnings and blockers",
                bullets=bullets,
                layout_hint="title_with_visual",
            ),
            PlannedSlide(
                slide_id="slide_002",
                slide_type=SlideType.CONTENT,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Operator review remains explicit and safe",
                bullets=bullets[:3],
                layout_hint="content_with_visual",
            ),
        ),
    )


def render_calibration_pptx():
    quality = improve_presentation_plan_render_quality(
        calibration_plan(),
        profile=build_default_k3_quality_profile(template_id="business_clean"),
    )
    render = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=quality.render_plan,
            plan_snapshot_id="rch3_test_plan",
            render_mode="adaptive",
            template_id=quality.profile.template_id,
            artifact_filename="rch3-test.pptx",
        )
    )
    return quality, render


def test_rch3_checker_reports_ready_without_scope_escape() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "RCH3"
    assert payload["status"] == "ready"
    assert payload["rch3_visual_qa_heuristic_calibration_supported"] is True
    assert payload["visual_qa_issue_severity_calibration_supported"] is True
    assert payload["api_endpoint_added_by_rch3"] is False
    assert payload["db_schema_migration_added_by_rch3"] is False
    assert payload["frontend_runtime_changed_by_rch3"] is False
    assert payload["dependency_versions_changed_by_rch3"] is False
    assert payload["dockerfiles_changed_by_rch3"] is False
    assert payload["cloud_vision_added_by_rch3"] is False
    assert payload["kimi_level_claimed_by_rch3"] is False


def test_rch3_policy_separates_info_warning_and_blocker_status() -> None:
    policy = VisualQAPolicy()
    info_only = tuple(
        VisualQAIssue("rch3.info", "info", "slide_001", "minor", "inspect only")
        for _ in range(policy.max_info_count_to_pass)
    )
    assert _status_for(score=_score_issues(info_only), issues=info_only, policy=policy) == "passed"

    warnings = tuple(
        VisualQAIssue("rch3.warning", "warning", "slide_001", "warning", "review")
        for _ in range(policy.max_warning_count_to_pass + 1)
    )
    assert _status_for(score=_score_issues(warnings), issues=warnings, policy=policy) == "needs_operator_review"

    blockers = (VisualQAIssue("rch3.blocker", "blocker", "slide_001", "blocker", "rework"),)
    assert _status_for(score=_score_issues(blockers), issues=blockers, policy=policy) == "blocked"


def test_rch3_runtime_emits_calibrated_safe_metadata() -> None:
    quality, render = render_calibration_pptx()
    result = run_visual_qa_runtime(
        VisualQARuntimeRequest(
            plan=quality.render_plan,
            artifact_content=render.artifact_content,
            plan_snapshot_id="rch3_test_plan",
            render_mode="adaptive",
            template_id=quality.profile.template_id,
            artifact_filename="rch3-test.pptx",
        )
    )
    metadata = result.safe_metadata
    assert metadata["rch3_visual_qa_heuristic_calibration_supported"] is True
    assert metadata["visual_qa_issue_severity_calibration_supported"] is True
    assert metadata["visual_qa_false_positive_reduction_supported"] is True
    assert metadata["visual_qa_false_negative_guard_supported"] is True
    assert metadata["calibrated_issue_counts"]["info"] == metadata["info_count"]
    assert metadata["calibrated_issue_counts"]["warning"] == metadata["warning_count"]
    assert metadata["calibrated_issue_counts"]["blocker"] == metadata["blocker_count"]
    assert metadata["raw_slide_text_stored"] is False
    assert metadata["network_required"] is False
    assert result.status in {"passed", "needs_operator_review"}


def test_rch3_capabilities_keep_release_scope_bounded() -> None:
    capabilities = build_rch3_capabilities_report()
    assert capabilities["rch3_visual_qa_heuristic_calibration_supported"] is True
    assert capabilities["api_endpoint_added_by_rch3"] is False
    assert capabilities["db_schema_migration_added_by_rch3"] is False
    assert capabilities["frontend_runtime_changed_by_rch3"] is False
    assert capabilities["dependency_versions_changed_by_rch3"] is False
    assert capabilities["dockerfiles_changed_by_rch3"] is False
    assert capabilities["cloud_llm_added_by_rch3"] is False
    assert capabilities["cloud_vision_added_by_rch3"] is False
    assert capabilities["kimi_level_claimed_by_rch3"] is False
    assert capabilities["whole_project_kimi_level_supported_by_rch3"] is False
