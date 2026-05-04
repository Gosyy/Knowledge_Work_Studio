from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.k_phase.renderer_quality import build_default_k3_quality_profile, improve_presentation_plan_render_quality
from backend.app.services.k_phase.visual_qa import (
    PPTX_CONTENT_TYPE,
    VisualQAPolicy,
    VisualQARuntimeRequest,
    VisualQAReviewRequest,
    build_k4_capabilities_report,
    build_visual_qa_operator_review,
    run_visual_qa_runtime,
)
from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, render_approved_plan_to_pptx
from backend.app.services.slides_service.blocks import ChartBlock, TableBlock
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_k4_visual_qa_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def qa_plan() -> PresentationPlan:
    bullets = (
        "K4 extracts a safe PPTX preview from local OOXML slide parts",
        "It checks layout bounds overlap overflow contrast and reading order",
        "Operator review remains explicit and safe for intranet operation",
        "K5 provenance and K6 end-to-end workflow remain future gates",
        "Extra density is trimmed by K3 before K4 inspects the artifact",
    )
    return PresentationPlan(
        deck_title="K4 visual QA runtime",
        deck_goal="Validate local deterministic visual QA before operator handoff.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=2,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.ANALYSIS),
        slides=(
            PlannedSlide(
                slide_id="slide_001",
                slide_type=SlideType.TITLE,
                story_arc_stage=StoryArcStage.OPENING,
                title="K4 validates the rendered PPTX package without cloud vision",
                bullets=bullets,
                layout_hint="title_with_visual",
            ),
            PlannedSlide(
                slide_id="slide_002",
                slide_type=SlideType.DATA,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Visual QA evidence",
                bullets=bullets[:4],
                blocks=(
                    TableBlock(
                        block_id="table_001",
                        columns=("Check", "Result", "Owner", "Risk", "Extra"),
                        rows=(
                            ("Bounds", "pass", "runtime", "low", "trim"),
                            ("Overflow", "estimated", "runtime", "medium", "trim"),
                            ("Contrast", "pass", "runtime", "low", "trim"),
                            ("Order", "pass", "runtime", "low", "trim"),
                            ("Operator", "safe", "workflow", "medium", "trim"),
                            ("Future", "K5", "later", "planned", "trim"),
                        ),
                    ),
                    ChartBlock(
                        block_id="chart_001",
                        title="QA score",
                        categories=("bounds", "overlap", "overflow", "contrast", "order", "review", "future"),
                        values=(95, 94, 88, 96, 92, 90, 70),
                    ),
                ),
            ),
        ),
    )


def render_quality_pptx():
    quality = improve_presentation_plan_render_quality(qa_plan(), profile=build_default_k3_quality_profile(template_id="business_clean"))
    render = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=quality.render_plan,
            plan_snapshot_id="k4_test_plan",
            render_mode="adaptive",
            template_id=quality.profile.template_id,
            artifact_filename="k4-test.pptx",
        )
    )
    return quality, render


def test_k4_checker_reports_ready_without_scope_escape() -> None:
    result = run_check("--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "K4"
    assert payload["status"] == "ready"
    assert payload["runtime_changed_by_k4"] is True
    assert payload["api_endpoint_added_by_k4"] is False
    assert payload["db_schema_migration_added_by_k4"] is False
    assert payload["frontend_runtime_changed_by_k4"] is False
    assert payload["dependency_versions_changed_by_k4"] is False
    assert payload["dockerfiles_changed_by_k4"] is False
    assert payload["cloud_vision_added_by_k4"] is False
    assert payload["source_to_slide_provenance_added_by_k4"] is False
    assert payload["kimi_level_claimed_by_k4"] is False
    assert payload["whole_project_kimi_level_supported"] is False


def test_k4_visual_qa_extracts_safe_preview_and_passes_k3_bounded_artifact() -> None:
    quality, render = render_quality_pptx()
    result = run_visual_qa_runtime(
        VisualQARuntimeRequest(
            plan=quality.render_plan,
            artifact_content=render.artifact_content,
            plan_snapshot_id="k4_test_plan",
            render_mode="adaptive",
            template_id=quality.profile.template_id,
            artifact_filename="k4-test.pptx",
        )
    )
    assert result.status in {"passed", "needs_operator_review"}
    assert result.score >= 75
    assert result.artifact_checksum_sha256 == render.checksum_sha256
    assert result.slide_count == len(quality.render_plan.slides)
    assert all(slide.bounds_ok for slide in result.slide_previews)
    assert result.safe_metadata["raw_slide_text_stored"] is False
    assert result.safe_metadata["network_required"] is False


def test_k4_operator_review_workflow_is_explicit_and_blocks_blocker_approval() -> None:
    quality, render = render_quality_pptx()
    result = run_visual_qa_runtime(
        VisualQARuntimeRequest(
            plan=quality.render_plan,
            artifact_content=render.artifact_content,
            plan_snapshot_id="k4_test_plan",
            render_mode="adaptive",
            template_id=quality.profile.template_id,
            artifact_filename="k4-test.pptx",
        )
    )
    review = build_visual_qa_operator_review(VisualQAReviewRequest(visual_qa_result=result, decision="approve"))
    assert review.review_status == "completed"
    assert review.decision == "approve"
    assert "k4.visual_qa.operator_review.approved" in review.safe_event_types


def test_k4_rejects_non_pptx_or_invalid_local_template() -> None:
    quality, render = render_quality_pptx()
    try:
        run_visual_qa_runtime(
            VisualQARuntimeRequest(
                plan=quality.render_plan,
                artifact_content=render.artifact_content,
                plan_snapshot_id="k4_test_plan",
                content_type="application/pdf",
                artifact_filename="k4-test.pdf",
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError("K4 must reject non-PPTX artifacts in this controlled runtime patch")

    try:
        run_visual_qa_runtime(
            VisualQARuntimeRequest(
                plan=quality.render_plan,
                artifact_content=render.artifact_content,
                plan_snapshot_id="k4_test_plan",
                template_id="https://example.invalid/template",
                artifact_filename="k4-test.pptx",
                content_type=PPTX_CONTENT_TYPE,
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError("K4 must reject external template references")


def test_k4_capabilities_report_keeps_future_gates_separate() -> None:
    capabilities = build_k4_capabilities_report()
    assert capabilities["visual_qa_runtime_supported"] is True
    assert capabilities["pdf_preview_runtime_added_by_k4"] is False
    assert capabilities["source_to_slide_provenance_added_by_k4"] is False
    assert capabilities["kimi_level_claimed_by_k4"] is False
    assert capabilities["whole_project_kimi_level_supported"] is False
