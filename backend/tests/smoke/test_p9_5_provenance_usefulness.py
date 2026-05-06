from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.k_phase.renderer_quality import build_default_k3_quality_profile, improve_presentation_plan_render_quality
from backend.app.services.k_phase.source_to_slide_provenance import build_source_to_slide_provenance, validate_k5_source_to_slide_result
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_p9_5_provenance_usefulness_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def useful_plan() -> PresentationPlan:
    return PresentationPlan(
        deck_title="P9-5 evidence cards",
        deck_goal="Make provenance useful for operator review.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=3,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.ANALYSIS, StoryArcStage.CLOSE),
        slides=(
            PlannedSlide(slide_id="slide_001", slide_type=SlideType.TITLE, story_arc_stage=StoryArcStage.OPENING, title="Approval gates protect source-backed generation", bullets=("approval gates", "source backed generation"), layout_hint="title_with_visual"),
            PlannedSlide(slide_id="slide_002", slide_type=SlideType.CONTENT, story_arc_stage=StoryArcStage.ANALYSIS, title="Evidence cards make provenance reviewable", bullets=("evidence cards", "operator review"), layout_hint="content_with_visual"),
            PlannedSlide(slide_id="slide_003", slide_type=SlideType.CONCLUSION, story_arc_stage=StoryArcStage.CLOSE, title="Release evidence remains offline and bounded", bullets=("offline runtime", "bounded excerpts"), layout_hint="conclusion"),
        ),
    )


def useful_result():
    quality = improve_presentation_plan_render_quality(useful_plan(), profile=build_default_k3_quality_profile(template_id="business_clean"))
    return build_source_to_slide_provenance(
        quality.render_plan,
        source_text=(
            "Approval gates protect source backed generation before rendering starts. "
            "Evidence cards make provenance reviewable by pairing each slide claim with a bounded excerpt. "
            "Release evidence remains offline and bounded through digest backed manifest entries."
        ),
        source_refs=({"kind": "document", "source_id": "memo_p9_5", "title": "Evidence memo", "locator": "memo.md#p9-5"},),
    )


def unrelated_result():
    quality = improve_presentation_plan_render_quality(useful_plan(), profile=build_default_k3_quality_profile(template_id="business_clean"))
    return build_source_to_slide_provenance(
        quality.render_plan,
        source_text="Unrelated procurement memo. Warehouse lighting update. Cafeteria vendor rotation.",
        source_refs=({"kind": "document", "source_id": "memo_unrelated", "title": "Unrelated memo"},),
    )


def test_p9_5_checker_reports_ready_without_scope_escape() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P9-5"
    assert payload["status"] == "ready"
    assert payload["p9_5_operator_evidence_review_supported"] is True
    assert payload["operator_evidence_cards_supported"] is True
    assert payload["evidence_review_manifest_section_supported"] is True
    assert payload["api_endpoint_added_by_p9_5"] is False
    assert payload["db_schema_migration_added_by_p9_5"] is False
    assert payload["frontend_runtime_changed_by_p9_5"] is False
    assert payload["dependency_versions_changed_by_p9_5"] is False
    assert payload["dockerfiles_changed_by_p9_5"] is False
    assert payload["cloud_llm_added_by_p9_5"] is False
    assert payload["cloud_vision_added_by_p9_5"] is False
    assert payload["kimi_level_claimed_by_p9_5"] is False


def test_p9_5_manifest_contains_operator_evidence_cards() -> None:
    result = useful_result()
    assert validate_k5_source_to_slide_result(result) == []
    evidence_review = result.manifest_section["operator_evidence_review"]
    cards = evidence_review["evidence_cards"]
    assert evidence_review["checkpoint"] == "P9-5"
    assert len(cards) == len(result.plan.slides)
    assert evidence_review["summary"]["card_count"] == len(cards)
    for card in cards:
        assert card["slide_id"].startswith("slide_")
        assert card["citation_id"].startswith("k5_cite_")
        assert card["claim_preview"]
        assert card["excerpt_preview"]
        assert 1 <= card["usefulness_score"] <= 5
        assert card["review_priority"] in {"spot_check", "operator_review"}
        assert "operator" in card["review_hint"].lower()


def test_p9_5_safe_metadata_has_aggregate_evidence_usefulness_only() -> None:
    result = useful_result()
    metadata = result.safe_metadata
    encoded = json.dumps(metadata, ensure_ascii=False, sort_keys=True).lower()
    assert metadata["p9_5_operator_evidence_review_supported"] is True
    assert metadata["operator_evidence_card_count"] == len(result.plan.slides)
    assert metadata["evidence_usefulness_score_min"] >= 3
    assert metadata["low_usefulness_evidence_card_count"] == 0
    assert metadata["operator_evidence_review_required"] is False
    assert "approval gates protect" not in encoded
    assert metadata["raw_source_text_stored"] is False
    assert metadata["network_required"] is False
    assert metadata["kimi_level_claimed_by_p9_5"] is False


def test_p9_5_low_usefulness_evidence_requires_operator_review() -> None:
    result = unrelated_result()
    metadata = result.safe_metadata
    evidence_review = result.manifest_section["operator_evidence_review"]
    assert metadata["operator_evidence_card_count"] == len(result.plan.slides)
    assert metadata["operator_evidence_review_required"] is True
    assert metadata["low_usefulness_evidence_card_count"] >= 1
    assert evidence_review["summary"]["operator_evidence_review_required"] is True
    assert any(card["review_priority"] == "operator_review" for card in evidence_review["evidence_cards"])
