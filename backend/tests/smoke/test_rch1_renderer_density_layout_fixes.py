from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.k_phase.renderer_quality import build_default_k3_quality_profile, improve_presentation_plan_render_quality, select_layout_hint
from backend.app.services.slides_service.blocks import ComparisonBlock, TableBlock
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_rch1_checker_reports_ready() -> None:
    root = repo_root()
    result = subprocess.run([sys.executable, "scripts/kw_rch1_renderer_density_layout_check.py", "--repo-root", str(root), "--require-ready", "--json"], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "RCH1"
    assert payload["status"] == "ready"
    assert payload["renderer_density_layout_fixes_supported"] is True
    assert payload["api_endpoint_added_by_rch1"] is False
    assert payload["db_schema_migration_added_by_rch1"] is False
    assert payload["frontend_runtime_changed_by_rch1"] is False
    assert payload["dependency_versions_changed_by_rch1"] is False
    assert payload["dockerfiles_changed_by_rch1"] is False
    assert payload["cloud_llm_added_by_rch1"] is False
    assert payload["whole_project_kimi_level_supported"] is False


def test_rch1_promotes_comparison_like_gigachat_plan_to_comparison_layout() -> None:
    plan = PresentationPlan(
        deck_title="Renderer comparison",
        deck_goal="Verify comparison-like GigaChat plans get comparison layout.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=1,
        story_arc=(StoryArcStage.ANALYSIS,),
        slides=(
            PlannedSlide(
                slide_id="cmp",
                slide_type=SlideType.CONTENT,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Compare current document flow versus target operator workflow",
                bullets=(
                    "Current path: dense source notes and weak hierarchy make slides hard to review",
                    "Target path: renderer selects a bounded comparison layout with clear tradeoffs",
                    "Decision: prioritize layout family selection before later visual QA checks",
                    "Risk: unbounded model bullets can still overload deterministic slide rendering",
                    "Overflow detail that should be moved out of visible body text",
                ),
            ),
        ),
    )
    profile = build_default_k3_quality_profile(template_id="business_clean")
    result = improve_presentation_plan_render_quality(plan, profile=profile)
    slide = result.render_plan.slides[0]
    assert select_layout_hint(plan.slides[0]) == "two_column_comparison"
    assert slide.layout_hint == "two_column_comparison"
    assert any(isinstance(block, ComparisonBlock) for block in slide.blocks)
    assert len(slide.bullets) <= profile.density_policy.max_bullets_per_slide
    assert "overflow item" in (slide.speaker_notes or "")


def test_rch1_bounds_table_density_and_reports_layout_families() -> None:
    plan = PresentationPlan(
        deck_title="Data density",
        deck_goal="Verify table-heavy renderer density fixes.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=1,
        story_arc=(StoryArcStage.ANALYSIS,),
        slides=(
            PlannedSlide(
                slide_id="data",
                slide_type=SlideType.DATA,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Coverage table and chart data signals",
                bullets=("coverage ratio 1.0", "visual QA score 80", "warnings 5", "artifacts 3"),
                blocks=(TableBlock(block_id="wide", columns=("A", "B", "C", "D", "E"), rows=(("1", "2", "3", "4", "5"),) * 9),),
            ),
        ),
    )
    profile = build_default_k3_quality_profile(template_id="business_clean")
    result = improve_presentation_plan_render_quality(plan, profile=profile)
    slide = result.render_plan.slides[0]
    table = next(block for block in slide.blocks if isinstance(block, TableBlock))
    assert slide.layout_hint == "data_summary"
    assert len(table.columns) <= profile.density_policy.max_table_columns
    assert len(table.rows) <= profile.density_policy.max_table_rows
    assert result.safe_metadata["rch1_renderer_density_layout_fixes_supported"] is True
    assert result.safe_metadata["rch1_layout_family_distribution"]["data_summary"] == 1
