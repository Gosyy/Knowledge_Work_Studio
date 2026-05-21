from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.k_phase.renderer_quality import build_default_k3_quality_profile, improve_presentation_plan_render_quality
from backend.app.services.k_phase.source_to_slide_provenance import build_source_to_slide_provenance
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_p9_6_semantic_source_coverage_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def coverage_plan(*, include_late_signals: bool = True) -> PresentationPlan:
    if include_late_signals:
        slides = (
            PlannedSlide(slide_id="slide_001", slide_type=SlideType.TITLE, story_arc_stage=StoryArcStage.OPENING, title="K4 visual QA and K5 provenance are covered", bullets=("visual QA", "provenance evidence"), layout_hint="title_with_visual"),
            PlannedSlide(slide_id="slide_002", slide_type=SlideType.CONTENT, story_arc_stage=StoryArcStage.ANALYSIS, title="K6 workflow closes the operator gate", bullets=("end-to-end workflow", "operator gate"), layout_hint="content_with_visual"),
            PlannedSlide(slide_id="slide_003", slide_type=SlideType.CONTENT, story_arc_stage=StoryArcStage.ANALYSIS, title="Closure readiness covers risks and guardrails", bullets=("release readiness", "risk guardrails"), layout_hint="content_with_visual"),
            PlannedSlide(slide_id="slide_004", slide_type=SlideType.CONCLUSION, story_arc_stage=StoryArcStage.CLOSE, title="Next actions preserve offline topology", bullets=("next actions", "offline intranet Server 3 GigaChat"), layout_hint="conclusion"),
        )
    else:
        slides = (
            PlannedSlide(slide_id="slide_001", slide_type=SlideType.TITLE, story_arc_stage=StoryArcStage.OPENING, title="K1 to K3 status only", bullets=("planning", "renderer quality"), layout_hint="title_with_visual"),
            PlannedSlide(slide_id="slide_002", slide_type=SlideType.CONTENT, story_arc_stage=StoryArcStage.ANALYSIS, title="Early implementation notes", bullets=("draft slides", "operator notes"), layout_hint="content_with_visual"),
            PlannedSlide(slide_id="slide_003", slide_type=SlideType.CONCLUSION, story_arc_stage=StoryArcStage.CLOSE, title="Early phase summary", bullets=("local runtime", "bounded generation"), layout_hint="conclusion"),
        )
    return PresentationPlan(
        deck_title="P9-6 semantic source coverage",
        deck_goal="Verify late source signals are not lost behind complete technical provenance.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=len(slides),
        story_arc=tuple(slide.story_arc_stage for slide in slides),
        slides=slides,
    )


def late_source_text() -> str:
    return (
        "The project log includes K4 visual QA runtime, K5 source-to-slide provenance, and K6 end-to-end workflow. "
        "The release readiness closure verdict was accepted, but risks and guardrails still need operator review. "
        "Next actions include RC1 follow-up and offline intranet topology with Server 3 GigaChat."
    )


def provenance_result(*, include_late_signals: bool = True):
    quality = improve_presentation_plan_render_quality(
        coverage_plan(include_late_signals=include_late_signals),
        profile=build_default_k3_quality_profile(template_id="business_clean"),
    )
    return build_source_to_slide_provenance(
        quality.render_plan,
        source_text=late_source_text(),
        source_refs=({"kind": "document", "source_id": "project_log", "title": "Project log", "locator": "log.md#p9-6"},),
    )


def test_p9_6_checker_reports_ready_without_scope_escape() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P9-6"
    assert payload["status"] == "ready"
    assert payload["p9_6_semantic_source_coverage_supported"] is True
    assert payload["semantic_source_signal_coverage_supported"] is True
    assert payload["late_source_section_guard_supported"] is True
    assert payload["api_endpoint_added_by_p9_6"] is False
    assert payload["db_schema_migration_added_by_p9_6"] is False
    assert payload["frontend_runtime_changed_by_p9_6"] is False
    assert payload["dependency_versions_changed_by_p9_6"] is False
    assert payload["dockerfiles_changed_by_p9_6"] is False
    assert payload["cloud_llm_added_by_p9_6"] is False
    assert payload["cloud_vision_added_by_p9_6"] is False
    assert payload["kimi_level_claimed_by_p9_6"] is False


def test_p9_6_manifest_contains_semantic_coverage_section() -> None:
    result = provenance_result(include_late_signals=True)
    coverage = result.manifest_section["semantic_source_coverage"]
    summary = coverage["summary"]
    assert coverage["checkpoint"] == "P9-6"
    assert summary["expected_signal_count"] >= 6
    assert summary["uncovered_signal_count"] == 0
    assert summary["coverage_status"] == "good"
    assert summary["human_semantic_coverage_review_required"] is False
    assert result.safe_metadata["p9_6_semantic_source_coverage_supported"] is True
    assert result.safe_metadata["semantic_source_coverage_status"] == "good"


def test_p9_6_missing_late_source_signals_require_operator_review() -> None:
    result = provenance_result(include_late_signals=False)
    coverage = result.manifest_section["semantic_source_coverage"]
    summary = coverage["summary"]
    uncovered = set(summary["uncovered_signal_ids"])
    assert summary["coverage_status"] == "needs_human_review"
    assert summary["human_semantic_coverage_review_required"] is True
    assert result.safe_metadata["human_semantic_coverage_review_required"] is True
    assert result.safe_metadata["semantic_source_uncovered_signal_count"] >= 3
    assert {"visual_qa_k4", "provenance_k5", "workflow_k6"}.issubset(uncovered)


def test_p9_6_safe_metadata_is_aggregate_only() -> None:
    result = provenance_result(include_late_signals=True)
    encoded = json.dumps(result.safe_metadata, ensure_ascii=False, sort_keys=True).lower()
    assert "the project log includes" not in encoded
    assert "server 3 gigachat" not in encoded
    assert result.safe_metadata["raw_source_text_stored"] is False
    assert result.safe_metadata["network_required"] is False
    assert result.safe_metadata["kimi_level_claimed_by_p9_6"] is False
