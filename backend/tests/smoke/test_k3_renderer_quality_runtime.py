from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.k_phase.renderer_quality import (
    build_default_k3_quality_profile,
    improve_presentation_plan_render_quality,
    select_layout_hint,
)
from backend.app.services.slides_service.blocks import ChartBlock, TableBlock
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_k3_renderer_quality_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def dense_plan() -> PresentationPlan:
    bullets = (
        "This bullet contains too many words for a clean deterministic local slide body and should be bounded",
        "This second bullet also contains enough words to push the slide toward overloaded density",
        "This third bullet keeps adding detail that belongs in source notes or speaker notes instead",
        "This fourth bullet is still acceptable after trimming",
        "This fifth bullet should be removed by the K3 density policy",
    )
    return PresentationPlan(
        deck_title="Renderer quality runtime",
        deck_goal="Improve deterministic local rendering quality.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=2,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.ANALYSIS),
        slides=(
            PlannedSlide(
                slide_id="slide_001",
                slide_type=SlideType.CONTENT,
                story_arc_stage=StoryArcStage.OPENING,
                title="A very long title that should be bounded by the renderer quality profile before rendering to PPTX",
                bullets=bullets,
                layout_hint="title_and_bullets",
            ),
            PlannedSlide(
                slide_id="slide_002",
                slide_type=SlideType.DATA,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Table and chart quality",
                bullets=bullets[:4],
                blocks=(
                    TableBlock(
                        block_id="t1",
                        columns=("A", "B", "C", "D", "E"),
                        rows=(("1", "2", "3", "4", "5"),) * 7,
                    ),
                    ChartBlock(
                        block_id="c1",
                        title="Trend",
                        categories=("A", "B", "C", "D", "E", "F", "G", "H"),
                        values=(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0),
                    ),
                ),
            ),
        ),
    )


def test_k3_checker_reports_ready_without_scope_escape() -> None:
    result = run_check("--require-ready", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "K3"
    assert payload["status"] == "ready"
    assert payload["runtime_changed_by_k3"] is True
    assert payload["api_endpoint_added_by_k3"] is False
    assert payload["db_schema_migration_added_by_k3"] is False
    assert payload["frontend_runtime_changed_by_k3"] is False
    assert payload["dependency_versions_changed_by_k3"] is False
    assert payload["dockerfiles_changed_by_k3"] is False
    assert payload["visual_qa_runtime_added_by_k3"] is False
    assert payload["source_to_slide_provenance_added_by_k3"] is False
    assert payload["kimi_level_claimed_by_k3"] is False
    assert payload["whole_project_kimi_level_supported"] is False


def test_k3_density_and_overflow_policy_bounds_plan() -> None:
    profile = build_default_k3_quality_profile(template_id="business_clean")
    result = improve_presentation_plan_render_quality(dense_plan(), profile=profile)
    assert len(result.render_plan.slides) == 2
    assert result.safe_metadata["overflow_prevention_count"] >= 1
    assert all(len(slide.bullets) <= profile.density_policy.max_bullets_per_slide for slide in result.render_plan.slides)
    assert all(len(slide.title) <= profile.density_policy.max_title_chars for slide in result.render_plan.slides)
    assert result.safe_metadata["network_required"] is False


def test_k3_layout_selection_and_table_chart_bounds() -> None:
    profile = build_default_k3_quality_profile(template_id="business_clean")
    result = improve_presentation_plan_render_quality(dense_plan(), profile=profile)
    data_slide = result.render_plan.slides[1]
    table = data_slide.blocks[0]
    chart = data_slide.blocks[1]
    assert select_layout_hint(data_slide) == "data_summary"
    assert data_slide.layout_hint == "data_summary"
    assert len(table.columns) == profile.density_policy.max_table_columns
    assert len(table.rows) == profile.density_policy.max_table_rows
    assert len(chart.categories) == profile.density_policy.max_chart_categories
    assert len(chart.values) == profile.density_policy.max_chart_categories


def test_k3_rejects_external_or_missing_template_id() -> None:
    try:
        build_default_k3_quality_profile(template_id="https://example.invalid/template")
    except ValueError:
        pass
    else:
        raise AssertionError("K3 must reject external template references")

    try:
        build_default_k3_quality_profile(template_id="")
    except ValueError:
        pass
    else:
        raise AssertionError("K3 must require an explicit local template id")
