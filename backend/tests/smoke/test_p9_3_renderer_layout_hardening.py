from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.k_phase.local_gigachat_planner import K1PlanningRequest, LocalGigaChatPlanningEngine
from backend.app.services.k_phase.renderer_quality import improve_presentation_plan_render_quality
from backend.app.services.slides_service.blocks import ComparisonBlock, TableBlock
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

BANNED_LABELS = ("Current / Option A", "Target / Option B", "RCH1 structured data summary")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_cases() -> list[dict[str, object]]:
    return json.loads((repo_root() / "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json").read_text(encoding="utf-8"))


def case_by_id(case_id: str) -> dict[str, object]:
    return next(case for case in load_cases() if case["case_id"] == case_id)


def build_plan(case_id: str):
    case = case_by_id(case_id)
    result = LocalGigaChatPlanningEngine(None).plan(
        K1PlanningRequest(
            source_text=str(case["source_text"]),
            audience=str(case.get("audience") or "operator_review"),
            deck_goal=str(case.get("deck_goal") or "Create a source-grounded presentation plan."),
            target_slide_count=int(case.get("target_slide_count") or 7),
            source_refs=({"source_id": case_id, "title": str(case.get("title") or case_id)},),
        )
    )
    return result


def block_text(blocks: tuple[object, ...]) -> str:
    parts: list[str] = []
    for block in blocks:
        for attr in ("left_title", "right_title", "caption"):
            value = getattr(block, attr, None)
            if value:
                parts.append(str(value))
        if isinstance(block, TableBlock):
            parts.extend(str(column) for column in block.columns)
            parts.extend(str(cell) for row in block.rows for cell in row)
        if isinstance(block, ComparisonBlock):
            parts.extend(block.left_items)
            parts.extend(block.right_items)
    return "\n".join(parts)


def assert_no_banned_renderer_labels(text: str) -> None:
    lowered = text.lower()
    for label in BANNED_LABELS:
        assert label.lower() not in lowered
    assert "\nreview\n" not in f"\n{lowered}\n"


def test_p9_3_checker_reports_ready(tmp_path: Path) -> None:
    root = repo_root()
    artifacts_dir = tmp_path / "p9-3"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_p9_3_renderer_layout_hardening_check.py",
            "--repo-root",
            str(root),
            "--artifacts-dir",
            str(artifacts_dir),
            "--require-ready",
            "--json",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P9-3"
    assert payload["status"] == "ready"
    assert payload["p9_3_renderer_layout_hardening_supported"] is True
    assert payload["arbitrary_current_target_labels_removed"] is True
    assert payload["generic_review_placeholder_removed"] is True
    assert payload["decision_matrix_renderer_blocks_supported"] is True
    assert payload["title_slide_layout_preserved_supported"] is True
    assert payload["kimi_level_claimed_by_p9_3"] is False
    assert payload["whole_project_kimi_level_supported"] is False
    assert (artifacts_dir / "p9-3-renderer-layout-hardening.json").exists()


def test_p9_3_decision_matrix_render_blocks_are_not_raw_current_target_or_review_tables() -> None:
    plan_result = build_plan("k0_comparison_table_to_decision_deck")
    render = improve_presentation_plan_render_quality(plan_result.plan)
    rendered_text = "\n".join(block_text(slide.blocks) for slide in render.render_plan.slides)
    assert_no_banned_renderer_labels(rendered_text)

    title_slide = render.render_plan.slides[0]
    assert title_slide.slide_type is SlideType.TITLE
    assert title_slide.layout_hint in {"title_slide", "title_with_visual"}

    decision_slide = next(slide for slide in render.render_plan.slides if "Decision matrix" in slide.title)
    comparison = next(block for block in decision_slide.blocks if isinstance(block, ComparisonBlock))
    assert comparison.left_title == "Runtime options"
    assert comparison.right_title == "Decision criteria"
    assert "Direct local GigaChat" in comparison.left_items
    assert "LiteLLM gateway" in comparison.left_items
    assert "Cloud LLM" in comparison.left_items

    evidence_slide = next(slide for slide in render.render_plan.slides if "LiteLLM gateway" in slide.title)
    table = next(block for block in evidence_slide.blocks if isinstance(block, TableBlock))
    assert table.columns == ("Dimension", "Evidence", "Operator use")
    assert ("Strength", "Good provider abstraction and central routing", "Retain") in table.rows
    assert ("Weakness", "Adds one more runtime hop and operational surface", "Mitigate") in table.rows
    assert ("Recommendation", "Keep optional on Server 2", "Act") in table.rows
    assert render.safe_metadata["p9_3_renderer_layout_hardening_supported"] is True
    assert render.safe_metadata["p9_3_arbitrary_current_target_labels_removed"] is True
    assert render.safe_metadata["p9_3_generic_review_placeholder_removed"] is True


def test_p9_3_normalizes_existing_generic_rch1_blocks() -> None:
    plan = PresentationPlan(
        deck_title="P9-3 renderer cleanup",
        deck_goal="Verify old generic RCH1 block labels are normalized.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=2,
        story_arc=(StoryArcStage.ANALYSIS, StoryArcStage.ANALYSIS),
        slides=(
            PlannedSlide(
                slide_id="comparison",
                slide_type=SlideType.COMPARISON,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Decision matrix: runtime options",
                bullets=(
                    "Options: Direct local GigaChat; LiteLLM gateway; Unsupported local-model option; Cloud LLM; Manual slide creation",
                    "Compare each option by strength, weakness, and recommendation.",
                ),
                blocks=(
                    ComparisonBlock(
                        block_id="old_cmp",
                        left_title="Current / Option A",
                        left_items=("Direct local GigaChat", "LiteLLM gateway"),
                        right_title="Target / Option B",
                        right_items=("Strength, weakness, recommendation",),
                    ),
                ),
            ),
            PlannedSlide(
                slide_id="table",
                slide_type=SlideType.DATA,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Decision evidence",
                bullets=(
                    "Strength: Good provider abstraction and central routing",
                    "Weakness: Adds one more runtime hop and operational surface",
                    "Recommendation: Keep optional on Server 2",
                ),
                blocks=(
                    TableBlock(
                        block_id="old_table",
                        columns=("Signal", "Evidence", "Review"),
                        rows=(("S1", "Strength: Good provider abstraction", "review"),),
                        caption="RCH1 structured data summary",
                    ),
                ),
            ),
        ),
    )
    render = improve_presentation_plan_render_quality(plan)
    rendered_text = "\n".join(block_text(slide.blocks) for slide in render.render_plan.slides)
    assert_no_banned_renderer_labels(rendered_text)
    assert render.render_plan.slides[0].blocks[0].left_title == "Runtime options"
    table = render.render_plan.slides[1].blocks[0]
    assert isinstance(table, TableBlock)
    assert table.columns == ("Dimension", "Evidence", "Operator use")
