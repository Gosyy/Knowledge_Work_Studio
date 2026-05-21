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
        [sys.executable, "scripts/kw_rch2_provenance_fragment_quality_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def sample_plan() -> PresentationPlan:
    return PresentationPlan(
        deck_title="RCH2 provenance quality",
        deck_goal="Verify diverse source fragments.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=4,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.CONTEXT, StoryArcStage.ANALYSIS, StoryArcStage.CLOSE),
        slides=(
            PlannedSlide(slide_id="slide_001", slide_type=SlideType.TITLE, story_arc_stage=StoryArcStage.OPENING, title="Approval gates protect source-backed generation", bullets=("approval workflow", "source backed generation"), layout_hint="title_with_visual"),
            PlannedSlide(slide_id="slide_002", slide_type=SlideType.CONTENT, story_arc_stage=StoryArcStage.CONTEXT, title="Renderer density improves slide readability", bullets=("renderer density", "layout readability"), layout_hint="content_with_visual"),
            PlannedSlide(slide_id="slide_003", slide_type=SlideType.DATA, story_arc_stage=StoryArcStage.ANALYSIS, title="Visual QA catches overlap and contrast risks", bullets=("visual qa", "overlap contrast"), layout_hint="data_summary"),
            PlannedSlide(slide_id="slide_004", slide_type=SlideType.CONCLUSION, story_arc_stage=StoryArcStage.CLOSE, title="Provenance manifest keeps evidence reviewable", bullets=("provenance manifest", "evidence review"), layout_hint="conclusion"),
        ),
    )


def source_text() -> str:
    return (
        "Approval gates protect source backed generation before rendering starts. "
        "Renderer density improves slide readability by reducing bullets and selecting stronger layouts. "
        "Visual QA catches overlap contrast and reading order risks in local PPTX output. "
        "Provenance manifest keeps evidence reviewable through fragment digests and citation footers. "
        "Operators review low quality evidence links before release."
    )


def provenance_result():
    quality = improve_presentation_plan_render_quality(sample_plan(), profile=build_default_k3_quality_profile(template_id="business_clean"))
    return build_source_to_slide_provenance(
        quality.render_plan,
        source_text=source_text(),
        source_refs=(
            {"kind": "document", "source_id": "memo_a", "title": "Workflow memo", "locator": "memo-a.md"},
            {"kind": "document", "source_id": "memo_b", "title": "QA memo", "locator": "memo-b.md"},
        ),
    )


def test_rch2_checker_reports_ready_without_scope_escape() -> None:
    result = run_check("--require-ready", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "RCH2"
    assert payload["status"] == "ready"
    assert payload["rch2_provenance_fragment_quality_supported"] is True
    assert payload["fragment_quality_scoring_supported"] is True
    assert payload["fragment_diversity_guard_supported"] is True
    assert payload["unique_fragment_ratio"] >= 1.0
    assert payload["low_quality_link_count"] == 0
    assert payload["api_endpoint_added_by_rch2"] is False
    assert payload["db_schema_migration_added_by_rch2"] is False
    assert payload["frontend_runtime_changed_by_rch2"] is False
    assert payload["dependency_versions_changed_by_rch2"] is False
    assert payload["dockerfiles_changed_by_rch2"] is False
    assert payload["cloud_llm_added_by_rch2"] is False
    assert payload["cloud_vision_added_by_rch2"] is False
    assert payload["kimi_level_claimed_by_rch2"] is False


def test_rch2_selects_relevant_and_diverse_fragments() -> None:
    result = provenance_result()
    metadata = result.safe_metadata
    assert metadata["rch2_checkpoint"] == "RCH2"
    assert metadata["evidence_quality_status"] == "good"
    assert metadata["unique_fragment_ratio"] == 1.0
    assert metadata["low_quality_link_count"] == 0
    assert metadata["average_fragment_match_score"] >= 2
    assert len({link.fragment_id for link in result.slide_links}) == len(result.slide_links)
    assert result.slide_links[0].fragment_selection_reason == "term_overlap"
    assert result.slide_links[0].match_score >= 2
    assert all(link.excerpt_digest.startswith("sha256:") for link in result.slide_links)


def test_rch2_safe_metadata_does_not_store_raw_source_text() -> None:
    result = provenance_result()
    encoded = json.dumps(result.safe_metadata, ensure_ascii=False).lower()
    assert "approval gates protect" not in encoded
    assert "renderer density improves" not in encoded
    assert result.safe_metadata["network_required"] is False
