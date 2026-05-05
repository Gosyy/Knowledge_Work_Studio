#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/RCH2_PROVENANCE_FRAGMENT_QUALITY.md",
    "backend/app/services/k_phase/source_to_slide_provenance.py",
    "scripts/kw_rch2_provenance_fragment_quality_check.py",
    "backend/tests/smoke/test_rch2_provenance_fragment_quality.py",
)
EXPECTED_BASE_AFTER_RCH1 = "63a83bbfc20f0d2f3e93b781889443955cb833a0"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing RCH2 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch != "8_K_Phase":
            errors.append(f"expected branch 8_K_Phase, got {branch}")
    return errors


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.k_phase.renderer_quality import build_default_k3_quality_profile, improve_presentation_plan_render_quality
    from backend.app.services.k_phase.source_to_slide_provenance import (
        build_source_to_slide_provenance,
        validate_k5_source_to_slide_result,
    )
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

    plan = PresentationPlan(
        deck_title="RCH2 provenance quality",
        deck_goal="Verify evidence fragments are relevant and diverse.",
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
    source_text = (
        "Approval gates protect source backed generation before rendering starts. "
        "Renderer density improves slide readability by reducing bullets and selecting stronger layouts. "
        "Visual QA catches overlap contrast and reading order risks in local PPTX output. "
        "Provenance manifest keeps evidence reviewable through fragment digests and citation footers. "
        "Operators review low quality evidence links before release."
    )
    quality = improve_presentation_plan_render_quality(plan, profile=build_default_k3_quality_profile(template_id="business_clean"))
    provenance = build_source_to_slide_provenance(
        quality.render_plan,
        source_text=source_text,
        source_refs=(
            {"kind": "document", "source_id": "memo_a", "title": "Workflow memo", "locator": "memo-a.md"},
            {"kind": "document", "source_id": "memo_b", "title": "QA memo", "locator": "memo-b.md"},
        ),
    )
    validation_errors = validate_k5_source_to_slide_result(provenance)
    metadata = provenance.safe_metadata
    encoded = json.dumps(metadata, ensure_ascii=False, sort_keys=True).lower()
    errors = list(validation_errors)

    if metadata.get("rch2_checkpoint") != "RCH2":
        errors.append("RCH2 metadata checkpoint mismatch")
    if metadata.get("rch2_provenance_fragment_quality_supported") is not True:
        errors.append("RCH2 quality support marker missing")
    if metadata.get("fragment_quality_scoring_supported") is not True:
        errors.append("RCH2 fragment scoring marker missing")
    if metadata.get("fragment_diversity_guard_supported") is not True:
        errors.append("RCH2 diversity guard marker missing")
    if metadata.get("unique_fragment_ratio", 0) < 1.0:
        errors.append("RCH2 expected unique fragments for the smoke sample")
    if metadata.get("average_fragment_match_score", 0) < 2:
        errors.append("RCH2 expected meaningful slide-fragment match score")
    if metadata.get("low_quality_link_count") != 0:
        errors.append("RCH2 smoke sample should not produce low quality links")
    if metadata.get("evidence_quality_status") != "good":
        errors.append(f"RCH2 expected evidence quality status good, got {metadata.get('evidence_quality_status')}")
    if len({link.fragment_id for link in provenance.slide_links}) != len(provenance.slide_links):
        errors.append("RCH2 smoke sample should use one distinct fragment per slide")
    if "approval gates protect" in encoded:
        errors.append("RCH2 safe metadata contains raw source text")
    if metadata.get("network_required") is not False:
        errors.append("RCH2 must stay local/offline")
    if metadata.get("kimi_level_claimed_by_k5") is not False:
        errors.append("RCH2 must not change Kimi-level claim markers")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "rch2_provenance_fragment_quality_supported": metadata.get("rch2_provenance_fragment_quality_supported") is True,
        "fragment_quality_scoring_supported": metadata.get("fragment_quality_scoring_supported") is True,
        "fragment_diversity_guard_supported": metadata.get("fragment_diversity_guard_supported") is True,
        "slide_fragment_relevance_supported": metadata.get("slide_fragment_relevance_supported") is True,
        "evidence_usefulness_metadata_supported": metadata.get("evidence_usefulness_metadata_supported") is True,
        "unique_fragment_ratio": metadata.get("unique_fragment_ratio"),
        "source_diversity_ratio": metadata.get("source_diversity_ratio"),
        "average_fragment_match_score": metadata.get("average_fragment_match_score"),
        "low_quality_link_count": metadata.get("low_quality_link_count"),
        "repeated_fragment_count": metadata.get("repeated_fragment_count"),
        "evidence_quality_status": metadata.get("evidence_quality_status"),
        "coverage_status": provenance.coverage.coverage_status,
        "slide_count": len(provenance.plan.slides),
        "slide_evidence_link_count": len(provenance.slide_links),
        "api_endpoint_added_by_rch2": False,
        "db_schema_migration_added_by_rch2": False,
        "frontend_runtime_changed_by_rch2": False,
        "dependency_versions_changed_by_rch2": False,
        "dockerfiles_changed_by_rch2": False,
        "cloud_llm_added_by_rch2": False,
        "cloud_vision_added_by_rch2": False,
        "kimi_level_claimed_by_rch2": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = static_errors + list(smoke.get("errors", []))
    return {
        "mode": "rch2-provenance-fragment-quality",
        "phase": "release-candidate-hardening",
        "checkpoint": "RCH2",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_rch1": EXPECTED_BASE_AFTER_RCH1,
        "runtime_changed_by_rch2": True,
        "runtime_change_type": "provenance_fragment_quality_hardening",
        "status": "ready" if not errors else "failed",
        "errors": errors,
        **{key: value for key, value in smoke.items() if key not in {"status", "errors"}},
        "next_recommended_step": "RCH3 — Visual QA heuristic calibration",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RCH2 provenance fragment quality/diversity check.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"RCH2 provenance fragment quality: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
