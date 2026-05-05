#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "backend/app/services/k_phase/renderer_quality.py",
    "scripts/kw_rch1_renderer_density_layout_check.py",
    "backend/tests/smoke/test_rch1_renderer_density_layout_fixes.py",
    "docs/codex/RCH1_RENDERER_DENSITY_LAYOUT_FIXES.md",
)
EXPECTED_RC3_HOTFIX4_COMMIT = "2c037dad1edc034b1dab45c4d84055c55e9f46ae"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def commit_is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing RCH1 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch != "8_K_Phase":
            errors.append(f"expected branch 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_RC3_HOTFIX4_COMMIT:
            ancestor = commit_is_ancestor(repo_root, EXPECTED_RC3_HOTFIX4_COMMIT, head)
            if ancestor is False:
                errors.append(f"expected RC3 hotfix 4 commit {EXPECTED_RC3_HOTFIX4_COMMIT} to be an ancestor of HEAD {head}")
            elif ancestor is None:
                errors.append("could not verify RC3 hotfix 4 ancestry")
    return errors


def runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from backend.app.services.k_phase.renderer_quality import build_default_k3_quality_profile, improve_presentation_plan_render_quality, select_layout_hint
    from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, render_approved_plan_to_pptx
    from backend.app.services.slides_service.blocks import TableBlock
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

    dense_bullets = (
        "Current path: documents arrive as unstructured source packets with variable length and repeated context that overloads slides",
        "Target path: renderer chooses a bounded comparison layout and preserves only high signal points for the operator",
        "Risk: tables and long plans can exceed readable density when produced by a live planning model",
        "Decision: use deterministic layout families, overflow notes, and local-only metadata before visual QA",
        "Duplicate decision: use deterministic layout families, overflow notes, and local-only metadata before visual QA",
        "Extra detail that should not remain in the visible slide body after RCH1 density balancing",
    )
    plan = PresentationPlan(
        deck_title="RCH1 renderer density layout fixes",
        deck_goal="Verify hardening for renderer density and layout families.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=3,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.ANALYSIS, StoryArcStage.CLOSE),
        slides=(
            PlannedSlide(
                slide_id="rch1_comparison",
                slide_type=SlideType.CONTENT,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Compare current and target renderer layout behavior for dense GigaChat generated plans",
                bullets=dense_bullets,
                layout_hint="title_and_bullets",
            ),
            PlannedSlide(
                slide_id="rch1_data",
                slide_type=SlideType.CONTENT,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Data table coverage score and density trend need a structured layout",
                bullets=("coverage ratio 1.0", "visual QA score 82", "artifact size 24000", "warnings 5"),
            ),
            PlannedSlide(
                slide_id="rch1_table",
                slide_type=SlideType.DATA,
                story_arc_stage=StoryArcStage.CLOSE,
                title="Bound table rows and columns",
                bullets=dense_bullets[:3],
                blocks=(
                    TableBlock(
                        block_id="wide_table",
                        columns=("A", "B", "C", "D", "E", "F"),
                        rows=(("1", "2", "3", "4", "5", "6"),) * 8,
                    ),
                ),
            ),
        ),
    )
    profile = build_default_k3_quality_profile(render_mode="adaptive", template_id="business_clean")
    result = improve_presentation_plan_render_quality(plan, profile=profile)
    render = render_approved_plan_to_pptx(ApprovedPlanRenderRequest(plan=result.render_plan, plan_snapshot_id="rch1_renderer_density_layout", render_mode="adaptive", template_id="business_clean", artifact_filename="rch1-renderer-density-layout.pptx"))
    errors: list[str] = []
    comparison_slide = result.render_plan.slides[0]
    data_slide = result.render_plan.slides[1]
    table_slide = result.render_plan.slides[2]
    if comparison_slide.layout_hint != "two_column_comparison":
        errors.append(f"expected comparison layout, got {comparison_slide.layout_hint}")
    if data_slide.layout_hint != "data_summary":
        errors.append(f"expected data layout, got {data_slide.layout_hint}")
    if len(comparison_slide.bullets) > profile.density_policy.max_bullets_per_slide:
        errors.append("comparison slide still exceeds bullet policy")
    if "overflow item" not in (comparison_slide.speaker_notes or ""):
        errors.append("overflow marker not added to speaker notes")
    table = table_slide.blocks[0]
    if len(table.columns) > profile.density_policy.max_table_columns or len(table.rows) > profile.density_policy.max_table_rows:
        errors.append("table rows/columns were not bounded")
    metadata = result.safe_metadata
    if metadata.get("rch1_renderer_density_layout_fixes_supported") is not True:
        errors.append("RCH1 metadata flag missing")
    distribution = metadata.get("rch1_layout_family_distribution", {})
    if not isinstance(distribution, dict) or "two_column_comparison" not in distribution or "data_summary" not in distribution:
        errors.append("RCH1 layout family distribution missing expected families")
    if render.size_bytes <= 0:
        errors.append("RCH1 render smoke produced empty PPTX")
    if metadata.get("network_required") is not False:
        errors.append("RCH1 must remain offline/local")
    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "rch1_renderer_density_layout_fixes_supported": metadata.get("rch1_renderer_density_layout_fixes_supported") is True,
        "comparison_layout_selected": comparison_slide.layout_hint == "two_column_comparison",
        "data_layout_selected": data_slide.layout_hint == "data_summary",
        "overflow_notes_added": "overflow item" in (comparison_slide.speaker_notes or ""),
        "layout_family_distribution": distribution,
        "rendered_pptx_size_bytes": render.size_bytes,
        "select_layout_hint_comparison": select_layout_hint(plan.slides[0]),
        "network_required": False,
        "api_endpoint_added_by_rch1": False,
        "db_schema_migration_added_by_rch1": False,
        "frontend_runtime_changed_by_rch1": False,
        "dependency_versions_changed_by_rch1": False,
        "dockerfiles_changed_by_rch1": False,
        "cloud_llm_added_by_rch1": False,
        "kimi_level_claimed_by_rch1": False,
        "whole_project_kimi_level_supported": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    errors = static_errors(repo_root, require_ready)
    smoke = runtime_smoke(repo_root) if not errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors.extend(smoke.get("errors", []))
    return {
        "checkpoint": "RCH1",
        "schema_version": "rch1.renderer_density_layout_fixes.v1",
        "status": "ready" if not errors else "failed",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "base_after_rc3": EXPECTED_RC3_HOTFIX4_COMMIT,
        "runtime_smoke": smoke,
        "renderer_density_layout_fixes_supported": smoke.get("rch1_renderer_density_layout_fixes_supported") is True,
        "feature_scope": "renderer_density_layout_hardening_only",
        "api_endpoint_added_by_rch1": False,
        "db_schema_migration_added_by_rch1": False,
        "frontend_runtime_changed_by_rch1": False,
        "dependency_versions_changed_by_rch1": False,
        "dockerfiles_changed_by_rch1": False,
        "cloud_llm_added_by_rch1": False,
        "kimi_level_claimed_by_rch1": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
        "next_recommended_step": "RCH2 — provenance fragment quality/diversity fixes",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RCH1 renderer density/layout hardening check.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(Path(args.repo_root).expanduser().resolve(), args.require_ready)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
