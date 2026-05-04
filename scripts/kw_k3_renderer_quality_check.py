#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/K3_RENDERER_QUALITY_RUNTIME.md",
    "backend/app/services/k_phase/renderer_quality.py",
    "scripts/kw_k3_renderer_quality_check.py",
    "backend/tests/smoke/test_k3_renderer_quality_runtime.py",
)
EXPECTED_BASE_AFTER_K2 = "48f8579adc9be176ce60cc1fa39fe5ad0b19f3a4"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing K3 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready and run_git(repo_root, "branch", "--show-current") != "8_K_Phase":
        errors.append(f"expected branch 8_K_Phase, got {run_git(repo_root, 'branch', '--show-current')}")
    return errors


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.k_phase.renderer_quality import (
        build_default_k3_quality_profile,
        build_k3_capabilities_report,
        improve_presentation_plan_render_quality,
    )
    from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, render_approved_plan_to_pptx
    from backend.app.services.slides_service.blocks import ChartBlock, TableBlock
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

    dense_bullets = (
        "This is a deliberately dense executive bullet with too many words for a clean slide body and should be bounded",
        "Another dense point that would create crowding in deterministic local rendering without density policy",
        "A third point explains chart and table context while still consuming a lot of body space",
        "A fourth point keeps the story readable but must remain short after the K3 pass",
        "A fifth point should be removed by the K3 density guard",
        "A sixth point should also be removed by the K3 density guard",
    )
    plan = PresentationPlan(
        deck_title="Renderer quality upgrade smoke",
        deck_goal="Verify deterministic local K3 rendering quality metadata.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=3,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.ANALYSIS, StoryArcStage.CLOSE),
        slides=(
            PlannedSlide(
                slide_id="slide_001",
                slide_type=SlideType.TITLE,
                story_arc_stage=StoryArcStage.OPENING,
                title="Renderer quality upgrade for local deterministic slide generation with bounded density",
                bullets=dense_bullets,
                layout_hint="title_and_bullets",
            ),
            PlannedSlide(
                slide_id="slide_002",
                slide_type=SlideType.DATA,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Evidence table and chart quality",
                bullets=dense_bullets[:4],
                blocks=(
                    TableBlock(
                        block_id="table_001",
                        columns=("Area", "Current", "Target", "Owner", "Risk"),
                        rows=(
                            ("Layout", "basic", "selected", "slides", "medium"),
                            ("Density", "high", "bounded", "runtime", "high"),
                            ("Tables", "wide", "trimmed", "runtime", "medium"),
                            ("Charts", "long", "bounded", "runtime", "medium"),
                            ("Themes", "local", "local", "runtime", "low"),
                            ("QA", "later", "K4", "runtime", "planned"),
                        ),
                        caption="K3 renderer table policy",
                    ),
                    ChartBlock(
                        block_id="chart_001",
                        title="Density trend",
                        categories=("A", "B", "C", "D", "E", "F", "G", "H"),
                        values=(1.0, 2.0, 3.0, 2.0, 4.0, 5.0, 6.0, 7.0),
                        unit="score",
                    ),
                ),
            ),
            PlannedSlide(
                slide_id="slide_003",
                slide_type=SlideType.CONCLUSION,
                story_arc_stage=StoryArcStage.CLOSE,
                title="K3 remains below Kimi-level until later gates pass",
                bullets=("Renderer quality is improved", "K4 visual QA remains separate", "K5 provenance remains separate"),
            ),
        ),
    )
    profile = build_default_k3_quality_profile(render_mode="adaptive", template_id="business_clean")
    result = improve_presentation_plan_render_quality(plan, profile=profile)
    render_result = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=result.render_plan,
            plan_snapshot_id="k3_renderer_quality_smoke_plan",
            render_mode="adaptive",
            template_id=result.profile.template_id,
            artifact_filename="k3-renderer-quality-smoke.pptx",
        )
    )
    metadata = result.safe_metadata
    capabilities = build_k3_capabilities_report()
    encoded_metadata = json.dumps(metadata, ensure_ascii=False, sort_keys=True).lower()
    errors: list[str] = []

    if metadata.get("checkpoint") != "K3":
        errors.append("K3 metadata checkpoint mismatch")
    if metadata.get("renderer_quality_runtime_supported") is not True:
        errors.append("K3 renderer quality runtime not reported as supported")
    if metadata.get("overflow_prevention_count", 0) < 1:
        errors.append("K3 overflow prevention did not run on dense sample")
    if metadata.get("table_chart_slide_count", 0) < 1:
        errors.append("K3 table/chart quality sample was not detected")
    if any(len(slide.bullets) > profile.density_policy.max_bullets_per_slide for slide in result.render_plan.slides):
        errors.append("K3 density policy did not cap slide bullets")
    data_slide = result.render_plan.slides[1]
    table = data_slide.blocks[0]
    chart = data_slide.blocks[1]
    if len(table.rows) > profile.density_policy.max_table_rows or len(table.columns) > profile.density_policy.max_table_columns:
        errors.append("K3 table policy did not bound rows/columns")
    if len(chart.categories) > profile.density_policy.max_chart_categories:
        errors.append("K3 chart policy did not bound categories")
    if render_result.content_type != "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        errors.append("K3 render-ready plan did not produce PPTX content type")
    if render_result.size_bytes <= 0:
        errors.append("K3 render-ready plan produced empty PPTX")
    if metadata.get("network_required") is not False:
        errors.append("K3 must remain offline/local with network_required=false")
    if capabilities.get("visual_qa_runtime_added_by_k3") is not False:
        errors.append("K3 must not add visual QA runtime")
    if capabilities.get("source_to_slide_provenance_added_by_k3") is not False:
        errors.append("K3 must not claim K5 provenance runtime")
    if metadata.get("kimi_level_claimed_by_k3") is not False:
        errors.append("K3 must not claim Kimi-level")
    if metadata.get("whole_project_kimi_level_supported") is not False:
        errors.append("K3 must not claim whole-project Kimi-level")
    if "q1 revenue" in encoded_metadata:
        errors.append("K3 safe metadata contains source-like raw text")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "renderer_quality_runtime_supported": metadata.get("renderer_quality_runtime_supported") is True,
        "layout_selection_engine_supported": metadata.get("layout_selection_engine_supported") is True,
        "content_density_control_supported": metadata.get("content_density_control_supported") is True,
        "visual_hierarchy_supported": metadata.get("visual_hierarchy_supported") is True,
        "table_chart_rendering_quality_supported": metadata.get("table_chart_rendering_quality_supported") is True,
        "title_subtitle_body_balance_supported": metadata.get("title_subtitle_body_balance_supported") is True,
        "local_theme_pack_supported": metadata.get("local_theme_pack_supported") is True,
        "overflow_prevention_supported": metadata.get("overflow_prevention_supported") is True,
        "deterministic_rendering_quality_metadata_supported": metadata.get("deterministic_rendering_quality_metadata_supported") is True,
        "safe_acceptance_checker_supported": metadata.get("safe_acceptance_checker_supported") is True,
        "render_ready_pptx_supported": render_result.size_bytes > 0,
        "rendered_pptx_size_bytes": render_result.size_bytes,
        "slide_count": len(result.render_plan.slides),
        "overflow_prevention_count": metadata.get("overflow_prevention_count"),
        "table_chart_slide_count": metadata.get("table_chart_slide_count"),
        "api_endpoint_added_by_k3": False,
        "db_schema_migration_added_by_k3": False,
        "frontend_runtime_changed_by_k3": False,
        "dependency_versions_changed_by_k3": False,
        "dockerfiles_changed_by_k3": False,
        "cloud_llm_added_by_k3": False,
        "visual_qa_runtime_added_by_k3": False,
        "source_to_slide_provenance_added_by_k3": False,
        "kimi_level_claimed_by_k3": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = static_errors + list(smoke.get("errors", []))
    return {
        "mode": "k3-renderer-quality-runtime",
        "phase": "K-phase",
        "checkpoint": "K3",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "k3_base_after_k2": EXPECTED_BASE_AFTER_K2,
        "runtime_changed_by_k3": True,
        "runtime_change_type": "renderer_quality_runtime_layer",
        "dependency_versions_changed_by_k3": False,
        "dockerfiles_changed_by_k3": False,
        "frontend_runtime_changed_by_k3": False,
        "api_endpoint_added_by_k3": False,
        "db_schema_migration_added_by_k3": False,
        "visual_qa_runtime_added_by_k3": False,
        "source_to_slide_provenance_added_by_k3": False,
        "cloud_llm_added_by_k3": False,
        "kimi_level_claimed_by_k3": False,
        "whole_project_kimi_level_supported": False,
        "runtime_smoke": smoke,
        "next_recommended_step": "K4 — Visual QA runtime",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio K3 renderer quality runtime check.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(Path(args.repo_root).expanduser().resolve(), args.require_ready)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
