#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/P9_6_SEMANTIC_SOURCE_COVERAGE.md",
    "backend/app/services/k_phase/source_to_slide_provenance.py",
    "scripts/kw_p9_6_semantic_source_coverage_check.py",
    "backend/tests/smoke/test_p9_6_semantic_source_coverage.py",
)
EXPECTED_BASE_AFTER_P9_5 = "a126bcb33cfc94441d6d0edf41ee90edfccc041f"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P9-6 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready and run_git(repo_root, "branch", "--show-current") not in ("9_Product_Release_Hardening", "8_K_Phase"):
        errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {run_git(repo_root, 'branch', '--show-current')}")
    return errors


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.k_phase.renderer_quality import build_default_k3_quality_profile, improve_presentation_plan_render_quality
    from backend.app.services.k_phase.source_to_slide_provenance import build_source_to_slide_provenance
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

    plan = PresentationPlan(
        deck_title="P9-6 semantic source coverage",
        deck_goal="Verify late source coverage guard.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=4,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.ANALYSIS, StoryArcStage.ANALYSIS, StoryArcStage.CLOSE),
        slides=(
            PlannedSlide(slide_id="slide_001", slide_type=SlideType.TITLE, story_arc_stage=StoryArcStage.OPENING, title="K4 visual QA and K5 provenance are covered", bullets=("visual QA", "provenance evidence"), layout_hint="title_with_visual"),
            PlannedSlide(slide_id="slide_002", slide_type=SlideType.CONTENT, story_arc_stage=StoryArcStage.ANALYSIS, title="K6 workflow closes the operator gate", bullets=("end-to-end workflow", "operator gate"), layout_hint="content_with_visual"),
            PlannedSlide(slide_id="slide_003", slide_type=SlideType.CONTENT, story_arc_stage=StoryArcStage.ANALYSIS, title="Closure readiness covers risks and guardrails", bullets=("release readiness", "risk guardrails"), layout_hint="content_with_visual"),
            PlannedSlide(slide_id="slide_004", slide_type=SlideType.CONCLUSION, story_arc_stage=StoryArcStage.CLOSE, title="Next actions preserve offline topology", bullets=("next actions", "offline intranet Server 3 GigaChat"), layout_hint="conclusion"),
        ),
    )
    source_text = (
        "The project log includes K4 visual QA runtime, K5 source-to-slide provenance, and K6 end-to-end workflow. "
        "The release readiness closure verdict was accepted, but risks and guardrails still need operator review. "
        "Next actions include RC1 follow-up and offline intranet topology with Server 3 GigaChat."
    )
    quality = improve_presentation_plan_render_quality(plan, profile=build_default_k3_quality_profile(template_id="business_clean"))
    result = build_source_to_slide_provenance(
        quality.render_plan,
        source_text=source_text,
        source_refs=({"kind": "document", "source_id": "p9_6_source", "title": "P9-6 project log", "locator": "log.md#p9-6"},),
    )
    return _inspect_result(result)


def _inspect_result(result: Any) -> dict[str, Any]:
    errors: list[str] = []
    metadata = result.safe_metadata
    coverage = result.manifest_section.get("semantic_source_coverage", {})
    summary = coverage.get("summary", {}) if isinstance(coverage, dict) else {}
    encoded_metadata = json.dumps(metadata, ensure_ascii=False, sort_keys=True).lower()

    if metadata.get("p9_6_semantic_source_coverage_supported") is not True:
        errors.append("P9-6 support marker missing from safe metadata")
    if metadata.get("semantic_source_signal_coverage_supported") is not True:
        errors.append("semantic source signal marker missing")
    if coverage.get("checkpoint") != "P9-6":
        errors.append("manifest missing P9-6 semantic source coverage section")
    if summary.get("expected_signal_count", 0) < 6:
        errors.append("P9-6 smoke should detect late source signals")
    if summary.get("uncovered_signal_count") != 0:
        errors.append("P9-6 smoke should cover all expected semantic signals")
    if summary.get("coverage_status") != "good":
        errors.append("P9-6 smoke coverage should be good")
    if metadata.get("human_semantic_coverage_review_required") is not False:
        errors.append("P9-6 covered smoke must not require semantic coverage review")
    if "the project log includes" in encoded_metadata:
        errors.append("safe metadata must not store raw source text")
    for key in (
        "api_endpoint_added_by_p9_6",
        "db_schema_migration_added_by_p9_6",
        "frontend_runtime_changed_by_p9_6",
        "dependency_versions_changed_by_p9_6",
        "dockerfiles_changed_by_p9_6",
        "cloud_llm_added_by_p9_6",
        "cloud_vision_added_by_p9_6",
        "kimi_level_claimed_by_p9_6",
    ):
        if metadata.get(key) is not False:
            errors.append(f"P9-6 forbidden scope marker not false: {key}")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "p9_6_semantic_source_coverage_supported": metadata.get("p9_6_semantic_source_coverage_supported") is True,
        "semantic_source_signal_coverage_supported": metadata.get("semantic_source_signal_coverage_supported") is True,
        "late_source_section_guard_supported": metadata.get("late_source_section_guard_supported") is True,
        "human_semantic_coverage_review_supported": metadata.get("human_semantic_coverage_review_supported") is True,
        "semantic_source_expected_signal_count": metadata.get("semantic_source_expected_signal_count"),
        "semantic_source_covered_signal_count": metadata.get("semantic_source_covered_signal_count"),
        "semantic_source_uncovered_signal_count": metadata.get("semantic_source_uncovered_signal_count"),
        "semantic_source_coverage_status": metadata.get("semantic_source_coverage_status"),
        "human_semantic_coverage_review_required": metadata.get("human_semantic_coverage_review_required"),
        "api_endpoint_added_by_p9_6": False,
        "db_schema_migration_added_by_p9_6": False,
        "frontend_runtime_changed_by_p9_6": False,
        "dependency_versions_changed_by_p9_6": False,
        "dockerfiles_changed_by_p9_6": False,
        "cloud_llm_added_by_p9_6": False,
        "cloud_vision_added_by_p9_6": False,
        "kimi_level_claimed_by_p9_6": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = static_errors + list(smoke.get("errors", []))
    return {
        "mode": "p9-6-semantic-source-coverage",
        "phase": "P9 Product Release Hardening",
        "checkpoint": "P9-6",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p9_5": EXPECTED_BASE_AFTER_P9_5,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        **{key: value for key, value in smoke.items() if key not in {"status", "errors"}},
        "next_recommended_step": "P9-7 — remaining release-hardening or closure planning",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P9-6 semantic source coverage check.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"P9-6 semantic source coverage: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
