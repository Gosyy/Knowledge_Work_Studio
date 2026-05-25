from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.k_phase.visual_qa import (
    VisualQARuntimeRequest,
    _has_raw_csv_rendering_signature,
    build_p9_4_capabilities_report,
    run_visual_qa_runtime,
)
from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, render_approved_plan_to_pptx
from backend.app.services.slides_service.blocks import ComparisonBlock, TableBlock
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_p9_4_visual_qa_semantic_guard_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def bad_semantic_plan() -> PresentationPlan:
    return PresentationPlan(
        deck_title="P9-4 blocked semantic plan",
        deck_goal="Show that semantic red flags block visually clean artifacts.",
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
                bullets=("Additional source-grounded planning point 1", "Raw CSV-like decision table header"),
                layout_hint="title_with_visual",
            ),
            PlannedSlide(
                slide_id="slide_002",
                slide_type=SlideType.COMPARISON,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Weak comparison synthesis",
                bullets=("Direct local GigaChat", "Optional gateway", "unsupported local-model option"),
                layout_hint="two_column_comparison",
                blocks=(
                    ComparisonBlock(
                        block_id="slide_002_compare",
                        left_title="Current / Option A",
                        left_items=("Direct local GigaChat",),
                        right_title="Target / Option B",
                        right_items=("Recommended next step",),
                    ),
                    TableBlock(
                        block_id="slide_002_table",
                        columns=("Signal", "Evidence", "Review"),
                        rows=(("S1", "Option,Strength,Weakness,Recommendation", "review"),),
                        caption="RCH1 structured data summary",
                    ),
                ),
            ),
        ),
    )


def good_semantic_plan() -> PresentationPlan:
    return PresentationPlan(
        deck_title="P9-4 clean semantic plan",
        deck_goal="Show that source-specific decision content can pass the semantic guard.",
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
                bullets=("Server 3 remains the default local GigaChat runtime", "Server 2 remains optional gateway and heavy runtime node"),
                layout_hint="title_with_visual",
            ),
            PlannedSlide(
                slide_id="slide_002",
                slide_type=SlideType.COMPARISON,
                story_arc_stage=StoryArcStage.RECOMMENDATION,
                title="Decision matrix preserves runtime option trade-offs",
                bullets=("Use direct local GigaChat by default", "Keep LiteLLM optional", "Keep unsupported local-model option out of runtime scope"),
                layout_hint="two_column_comparison",
                blocks=(
                    ComparisonBlock(
                        block_id="slide_002_compare",
                        left_title="Runtime options",
                        left_items=("Direct local GigaChat", "Optional LiteLLM gateway"),
                        right_title="Decision criteria",
                        right_items=("Offline default", "No hidden public internet dependency"),
                    ),
                    TableBlock(
                        block_id="slide_002_table",
                        columns=("Option", "Strength", "Weakness", "Recommendation"),
                        rows=(("Direct GigaChat", "Offline default", "Local endpoint required", "Use by default"),),
                        caption="Decision matrix",
                    ),
                ),
            ),
        ),
    )


def qa_plan(plan: PresentationPlan, filename: str):
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


def test_p9_4_checker_reports_ready_without_scope_escape() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P9-4"
    assert payload["status"] == "ready"
    assert payload["p9_4_visual_qa_semantic_guard_supported"] is True
    assert payload["visual_qa_product_quality_guard_supported"] is True
    assert payload["visual_qa_semantic_issue_detection_supported"] is True
    assert payload["api_endpoint_added_by_p9_4"] is False
    assert payload["db_schema_migration_added_by_p9_4"] is False
    assert payload["frontend_runtime_changed_by_p9_4"] is False
    assert payload["dependency_versions_changed_by_p9_4"] is False
    assert payload["dockerfiles_changed_by_p9_4"] is False
    assert payload["cloud_llm_added_by_p9_4"] is False
    assert payload["cloud_vision_added_by_p9_4"] is False
    assert payload["kimi_level_claimed_by_p9_4"] is False


def test_p9_4_semantic_guard_blocks_visual_clean_known_red_flags() -> None:
    result = qa_plan(bad_semantic_plan(), "p9-4-bad-test.pptx")
    check_ids = {issue.check_id for issue in result.issues}
    assert result.status == "blocked"
    assert "p9_4.generic_fallback_label" in check_ids
    assert "p9_4.raw_csv_rendering" in check_ids
    assert "p9_4.arbitrary_current_target_layout" in check_ids
    assert "p9_4.generic_table_review_placeholder" in check_ids
    assert result.safe_metadata["semantic_review_guard_issue_count"] >= 4
    assert result.safe_metadata["semantic_review_guard_blocker_count"] >= 2
    assert result.safe_metadata["raw_slide_text_stored"] is False
    assert result.safe_metadata["network_required"] is False


def test_p9_4_semantic_guard_allows_source_specific_decision_matrix() -> None:
    result = qa_plan(good_semantic_plan(), "p9-4-good-test.pptx")
    assert result.safe_metadata["semantic_review_guard_issue_count"] == 0
    assert result.safe_metadata["semantic_review_guard_blocker_count"] == 0
    assert result.status in {"passed", "needs_operator_review"}




def test_p9_4_raw_csv_guard_allows_natural_decision_matrix_language() -> None:
    natural = "Compare each option by strength, weakness, and recommendation. Runtime options and decision criteria."
    raw_header = "Option,Strength,Weakness,Recommendation"
    assert _has_raw_csv_rendering_signature(natural.lower()) is False
    assert _has_raw_csv_rendering_signature(raw_header.lower()) is True



def test_p9_4_semantic_issues_keep_k6_operator_gate_issue_ids() -> None:
    result = qa_plan(bad_semantic_plan(), "p9-4-operator-gate-test.pptx")
    semantic_issues = [issue for issue in result.issues if issue.check_id.startswith("p9_4.")]
    assert semantic_issues
    assert all(issue.issue_id == issue.check_id for issue in semantic_issues)
    safe_payload = [issue.as_safe_dict() for issue in semantic_issues]
    assert all(item["issue_id"] == item["check_id"] for item in safe_payload)

def test_p9_4_capabilities_keep_release_scope_bounded() -> None:
    capabilities = build_p9_4_capabilities_report()
    assert capabilities["p9_4_visual_qa_semantic_guard_supported"] is True
    assert capabilities["visual_qa_product_quality_guard_supported"] is True
    assert capabilities["visual_qa_issue_id_compatibility_supported"] is True
    assert capabilities["visual_qa_raw_csv_false_positive_guard_supported"] is True
    assert capabilities["network_required_by_p9_4"] is False
    assert capabilities["api_endpoint_added_by_p9_4"] is False
    assert capabilities["db_schema_migration_added_by_p9_4"] is False
    assert capabilities["frontend_runtime_changed_by_p9_4"] is False
    assert capabilities["dependency_versions_changed_by_p9_4"] is False
    assert capabilities["dockerfiles_changed_by_p9_4"] is False
    assert capabilities["cloud_llm_added_by_p9_4"] is False
    assert capabilities["cloud_vision_added_by_p9_4"] is False
    assert capabilities["kimi_level_claimed_by_p9_4"] is False
    assert capabilities["whole_project_kimi_level_supported_by_p9_4"] is False
