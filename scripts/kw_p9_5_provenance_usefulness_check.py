#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/P9_5_PROVENANCE_USEFULNESS.md",
    "backend/app/services/k_phase/source_to_slide_provenance.py",
    "scripts/kw_p9_5_provenance_usefulness_check.py",
    "backend/tests/smoke/test_p9_5_provenance_usefulness.py",
)
EXPECTED_BASE_AFTER_P9_4 = "647342bc420192bdf0267ef7ac31344eec786daa"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P9-5 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready and run_git(repo_root, "branch", "--show-current") not in ("9_Product_Release_Hardening", "8_K_Phase"):
        errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {run_git(repo_root, 'branch', '--show-current')}")
    return errors


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.k_phase.renderer_quality import build_default_k3_quality_profile, improve_presentation_plan_render_quality
    from backend.app.services.k_phase.source_to_slide_provenance import build_source_to_slide_provenance, validate_k5_source_to_slide_result
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

    plan = PresentationPlan(
        deck_title="P9-5 provenance usefulness",
        deck_goal="Verify operator evidence cards support fast human validation.",
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
    source_text = (
        "Approval gates protect source backed generation before rendering starts. "
        "Evidence cards make provenance reviewable by pairing each slide claim with a bounded excerpt. "
        "Release evidence remains offline and bounded through digest backed manifest entries."
    )
    quality = improve_presentation_plan_render_quality(plan, profile=build_default_k3_quality_profile(template_id="business_clean"))
    result = build_source_to_slide_provenance(
        quality.render_plan,
        source_text=source_text,
        source_refs=(({"kind": "document", "source_id": "p9_5_source", "title": "P9-5 evidence memo", "locator": "memo.md#p9-5"}),)
    )
    return _inspect_result(result)


def _inspect_result(result: Any) -> dict[str, Any]:
    from backend.app.services.k_phase.source_to_slide_provenance import validate_k5_source_to_slide_result

    errors = validate_k5_source_to_slide_result(result)
    metadata = result.safe_metadata
    section = result.manifest_section
    evidence_review = section.get("operator_evidence_review", {})
    cards = evidence_review.get("evidence_cards", []) if isinstance(evidence_review, dict) else []
    summary = evidence_review.get("summary", {}) if isinstance(evidence_review, dict) else {}
    encoded_metadata = json.dumps(metadata, ensure_ascii=False, sort_keys=True).lower()

    if metadata.get("p9_5_operator_evidence_review_supported") is not True:
        errors.append("P9-5 support marker missing from safe metadata")
    if metadata.get("operator_evidence_cards_supported") is not True:
        errors.append("operator evidence card marker missing")
    if section.get("operator_evidence_review") is None:
        errors.append("manifest missing operator_evidence_review section")
    if len(cards) != len(result.plan.slides):
        errors.append("operator evidence card count must match slide count")
    if summary.get("card_count") != len(cards):
        errors.append("operator evidence summary card count mismatch")
    for card in cards:
        for key in ("slide_id", "citation_id", "claim_preview", "excerpt_preview", "usefulness_score", "review_priority", "review_hint"):
            if key not in card:
                errors.append(f"operator evidence card missing {key}")
        if card.get("usefulness_score", 0) < 1 or card.get("usefulness_score", 0) > 5:
            errors.append("operator evidence usefulness score outside 1..5")
    if metadata.get("operator_evidence_card_count") != len(cards):
        errors.append("safe metadata card count mismatch")
    if "approval gates protect" in encoded_metadata:
        errors.append("safe metadata must not store raw source text")
    for key in (
        "api_endpoint_added_by_p9_5",
        "db_schema_migration_added_by_p9_5",
        "frontend_runtime_changed_by_p9_5",
        "dependency_versions_changed_by_p9_5",
        "dockerfiles_changed_by_p9_5",
        "cloud_llm_added_by_p9_5",
        "cloud_vision_added_by_p9_5",
        "kimi_level_claimed_by_p9_5",
    ):
        if metadata.get(key) is not False:
            errors.append(f"P9-5 forbidden scope marker not false: {key}")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "p9_5_operator_evidence_review_supported": metadata.get("p9_5_operator_evidence_review_supported") is True,
        "operator_evidence_cards_supported": metadata.get("operator_evidence_cards_supported") is True,
        "evidence_review_manifest_section_supported": metadata.get("evidence_review_manifest_section_supported") is True,
        "human_provenance_usefulness_hardening_supported": metadata.get("human_provenance_usefulness_hardening_supported") is True,
        "operator_evidence_card_count": metadata.get("operator_evidence_card_count"),
        "low_usefulness_evidence_card_count": metadata.get("low_usefulness_evidence_card_count"),
        "operator_evidence_review_required": metadata.get("operator_evidence_review_required"),
        "evidence_usefulness_score_min": metadata.get("evidence_usefulness_score_min"),
        "evidence_usefulness_score_average": metadata.get("evidence_usefulness_score_average"),
        "api_endpoint_added_by_p9_5": False,
        "db_schema_migration_added_by_p9_5": False,
        "frontend_runtime_changed_by_p9_5": False,
        "dependency_versions_changed_by_p9_5": False,
        "dockerfiles_changed_by_p9_5": False,
        "cloud_llm_added_by_p9_5": False,
        "cloud_vision_added_by_p9_5": False,
        "kimi_level_claimed_by_p9_5": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = static_errors + list(smoke.get("errors", []))
    return {
        "mode": "p9-5-provenance-usefulness",
        "phase": "P9 Product Release Hardening",
        "checkpoint": "P9-5",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p9_4": EXPECTED_BASE_AFTER_P9_4,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        **{key: value for key, value in smoke.items() if key not in {"status", "errors"}},
        "next_recommended_step": "P9-6 — release dossier or remaining human-review hardening",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P9-5 provenance usefulness check.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"P9-5 provenance usefulness: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
