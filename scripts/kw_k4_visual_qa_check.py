#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/K4_VISUAL_QA_RUNTIME.md",
    "backend/app/services/k_phase/visual_qa.py",
    "scripts/kw_k4_visual_qa_check.py",
    "backend/tests/smoke/test_k4_visual_qa_runtime.py",
)
EXPECTED_BASE_AFTER_K3 = "2c57ff1bb3d8c8d911fea11555bce76d55ec800e"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing K4 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready and run_git(repo_root, "branch", "--show-current") != "8_K_Phase":
        errors.append(f"expected branch 8_K_Phase, got {run_git(repo_root, 'branch', '--show-current')}")
    return errors


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.k_phase.renderer_quality import build_default_k3_quality_profile, improve_presentation_plan_render_quality
    from backend.app.services.k_phase.visual_qa import (
        VisualQARuntimeRequest,
        VisualQAReviewRequest,
        build_k4_capabilities_report,
        build_visual_qa_operator_review,
        run_visual_qa_runtime,
    )
    from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, render_approved_plan_to_pptx
    from backend.app.services.slides_service.blocks import ChartBlock, TableBlock
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

    dense_bullets = (
        "Visual QA validates the locally rendered deck package without calling cloud vision or external preview services",
        "Layout bounds overlap text density contrast and reading order are checked deterministically from OOXML",
        "Operator review receives safe metadata and issue identifiers instead of raw source text",
        "K4 remains below Kimi-level until K5 provenance and K6 end-to-end gates pass",
        "This extra bullet should be bounded by K3 before K4 inspects the rendered PPTX",
    )
    plan = PresentationPlan(
        deck_title="K4 visual QA runtime smoke",
        deck_goal="Verify local deterministic visual QA over a rendered PPTX artifact.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=3,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.ANALYSIS, StoryArcStage.CLOSE),
        slides=(
            PlannedSlide(
                slide_id="slide_001",
                slide_type=SlideType.TITLE,
                story_arc_stage=StoryArcStage.OPENING,
                title="K4 Visual QA runtime validates rendered slides before operator handoff",
                bullets=dense_bullets,
                layout_hint="title_with_visual",
            ),
            PlannedSlide(
                slide_id="slide_002",
                slide_type=SlideType.DATA,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="QA checks cover tables charts and bounded layout",
                bullets=dense_bullets[:4],
                blocks=(
                    TableBlock(
                        block_id="table_001",
                        columns=("Check", "Signal", "Verdict", "Owner", "Risk"),
                        rows=(
                            ("Bounds", "OOXML boxes", "local", "runtime", "low"),
                            ("Overflow", "text fill", "estimated", "runtime", "medium"),
                            ("Contrast", "theme colors", "local", "runtime", "low"),
                            ("Order", "shape order", "local", "runtime", "low"),
                            ("Review", "operator", "safe", "workflow", "medium"),
                            ("Future", "visual image QA", "later", "K6", "planned"),
                        ),
                    ),
                    ChartBlock(
                        block_id="chart_001",
                        title="Visual QA score trend",
                        categories=("bounds", "overlap", "overflow", "contrast", "order", "review", "future"),
                        values=(95, 94, 88, 96, 92, 90, 70),
                        unit="score",
                    ),
                ),
            ),
            PlannedSlide(
                slide_id="slide_003",
                slide_type=SlideType.CONCLUSION,
                story_arc_stage=StoryArcStage.CLOSE,
                title="K4 adds runtime QA without claiming Kimi-level",
                bullets=("Visual QA runtime is local", "K5 provenance remains separate", "K6 end-to-end workflow remains separate"),
            ),
        ),
    )
    quality = improve_presentation_plan_render_quality(plan, profile=build_default_k3_quality_profile(template_id="business_clean"))
    render = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=quality.render_plan,
            plan_snapshot_id="k4_visual_qa_smoke_plan",
            render_mode="adaptive",
            template_id=quality.profile.template_id,
            artifact_filename="k4-visual-qa-smoke.pptx",
        )
    )
    qa = run_visual_qa_runtime(
        VisualQARuntimeRequest(
            plan=quality.render_plan,
            artifact_content=render.artifact_content,
            plan_snapshot_id="k4_visual_qa_smoke_plan",
            render_mode="adaptive",
            template_id=quality.profile.template_id,
            artifact_filename="k4-visual-qa-smoke.pptx",
        )
    )
    review = build_visual_qa_operator_review(
        VisualQAReviewRequest(
            visual_qa_result=qa,
            decision="approve" if qa.status != "blocked" else "request_rework",
            rejection_reason="blocker issue requires rework" if qa.status == "blocked" else None,
        )
    )
    capabilities = build_k4_capabilities_report()
    metadata = qa.safe_metadata
    encoded_metadata = json.dumps(metadata, ensure_ascii=False, sort_keys=True).lower()
    errors: list[str] = []

    if metadata.get("checkpoint") != "K4":
        errors.append("K4 metadata checkpoint mismatch")
    if metadata.get("visual_qa_runtime_supported") is not True:
        errors.append("K4 visual QA runtime not reported as supported")
    if qa.status not in {"passed", "needs_operator_review"}:
        errors.append(f"K4 smoke should not be blocked, got {qa.status}")
    if qa.score < 75:
        errors.append(f"K4 visual QA smoke score too low: {qa.score}")
    if qa.slide_count != len(quality.render_plan.slides):
        errors.append("K4 slide preview count mismatch")
    if not qa.slide_previews or not all(item.bounds_ok for item in qa.slide_previews):
        errors.append("K4 layout bounds check failed on K3-bounded sample")
    if metadata.get("artifact_checksum_sha256") != render.checksum_sha256:
        errors.append("K4 artifact checksum does not match rendered PPTX checksum")
    if metadata.get("operator_review_required") is not (qa.status != "passed"):
        errors.append("K4 operator review requirement metadata mismatch")
    if review.review_status != "completed":
        errors.append("K4 operator review workflow did not complete")
    if capabilities.get("cloud_vision_added_by_k4") is not False:
        errors.append("K4 must not add cloud vision")
    if capabilities.get("api_endpoint_added_by_k4") is not False:
        errors.append("K4 must not add API endpoint")
    if capabilities.get("db_schema_migration_added_by_k4") is not False:
        errors.append("K4 must not add DB schema migration")
    if capabilities.get("dependency_versions_changed_by_k4") is not False:
        errors.append("K4 must not change dependency versions")
    if capabilities.get("dockerfiles_changed_by_k4") is not False:
        errors.append("K4 must not change Dockerfiles")
    if capabilities.get("source_to_slide_provenance_added_by_k4") is not False:
        errors.append("K4 must not claim K5 provenance runtime")
    if capabilities.get("kimi_level_claimed_by_k4") is not False:
        errors.append("K4 must not claim Kimi-level")
    if metadata.get("whole_project_kimi_level_supported") is not False:
        errors.append("K4 must not claim whole-project Kimi-level")
    if "visual qa validates" in encoded_metadata:
        errors.append("K4 safe metadata contains raw slide/source text")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "visual_qa_runtime_supported": metadata.get("visual_qa_runtime_supported") is True,
        "pptx_preview_runtime_supported": metadata.get("pptx_preview_runtime_supported") is True,
        "layout_bounds_check_supported": metadata.get("layout_bounds_check_supported") is True,
        "major_overlap_check_supported": metadata.get("major_overlap_check_supported") is True,
        "overflow_check_supported": metadata.get("overflow_check_supported") is True,
        "contrast_check_supported": metadata.get("contrast_check_supported") is True,
        "reading_order_check_supported": metadata.get("reading_order_check_supported") is True,
        "operator_review_workflow_supported": metadata.get("operator_review_workflow_supported") is True,
        "safe_visual_qa_metadata_supported": metadata.get("safe_visual_qa_metadata_supported") is True,
        "visual_qa_status": qa.status,
        "visual_qa_score": qa.score,
        "slide_preview_count": len(qa.slide_previews),
        "issue_count": len(qa.issues),
        "operator_review_status": review.review_status,
        "api_endpoint_added_by_k4": False,
        "db_schema_migration_added_by_k4": False,
        "frontend_runtime_changed_by_k4": False,
        "dependency_versions_changed_by_k4": False,
        "dockerfiles_changed_by_k4": False,
        "cloud_llm_added_by_k4": False,
        "cloud_vision_added_by_k4": False,
        "source_to_slide_provenance_added_by_k4": False,
        "kimi_level_claimed_by_k4": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = static_errors + list(smoke.get("errors", []))
    return {
        "mode": "k4-visual-qa-runtime",
        "phase": "K-phase",
        "checkpoint": "K4",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "k4_base_after_k3": EXPECTED_BASE_AFTER_K3,
        "runtime_changed_by_k4": True,
        "runtime_change_type": "visual_qa_runtime_layer",
        "dependency_versions_changed_by_k4": False,
        "dockerfiles_changed_by_k4": False,
        "frontend_runtime_changed_by_k4": False,
        "api_endpoint_added_by_k4": False,
        "db_schema_migration_added_by_k4": False,
        "source_to_slide_provenance_added_by_k4": False,
        "cloud_llm_added_by_k4": False,
        "cloud_vision_added_by_k4": False,
        "kimi_level_claimed_by_k4": False,
        "whole_project_kimi_level_supported": False,
        "runtime_smoke": smoke,
        "next_recommended_step": "K5 — Source-to-slide provenance",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio K4 visual QA runtime check.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    report = build_report(repo_root, require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(f"K4 visual QA runtime status: {report['status']}")
        for error in report["errors"]:
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
