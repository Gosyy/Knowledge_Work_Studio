#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/K5_SOURCE_TO_SLIDE_PROVENANCE.md",
    "backend/app/services/k_phase/source_to_slide_provenance.py",
    "scripts/kw_k5_source_to_slide_provenance_check.py",
    "backend/tests/smoke/test_k5_source_to_slide_provenance.py",
)
EXPECTED_BASE_AFTER_K4 = "f85300b2497577d2034467cf356bebb77db98cc5"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing K5 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
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
        attach_k5_provenance_to_manifest,
        build_k5_capabilities_report,
        build_source_to_slide_provenance,
        validate_k5_source_to_slide_result,
    )
    from backend.app.services.k_phase.visual_qa import VisualQARuntimeRequest, run_visual_qa_runtime
    from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, render_approved_plan_to_pptx
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

    source_text = (
        "Customer churn dropped after the offline document workflow adopted approval gates. "
        "Renderer quality issues were concentrated in dense table slides before K3 bounded the content. "
        "Visual QA found no blocker after K4 checked layout bounds overlap contrast and reading order. "
        "Operators require slide-level source evidence before K6 can claim an end-to-end Kimi-like workflow."
    )
    plan = PresentationPlan(
        deck_title="K5 source-to-slide provenance smoke",
        deck_goal="Verify that every rendered slide can be traced to bounded source fragments.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=4,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.CONTEXT, StoryArcStage.ANALYSIS, StoryArcStage.CLOSE),
        slides=(
            PlannedSlide(
                slide_id="slide_001",
                slide_type=SlideType.TITLE,
                story_arc_stage=StoryArcStage.OPENING,
                title="Source-backed deck traceability starts at the title slide",
                bullets=("Approval gates frame the workflow", "Every slide needs evidence"),
                layout_hint="title_with_visual",
            ),
            PlannedSlide(
                slide_id="slide_002",
                slide_type=SlideType.CONTENT,
                story_arc_stage=StoryArcStage.CONTEXT,
                title="Renderer quality context is linked to source fragments",
                bullets=("Dense table slides were the risk", "K3 bounded the local renderer"),
                layout_hint="content_with_visual",
            ),
            PlannedSlide(
                slide_id="slide_003",
                slide_type=SlideType.DATA,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Visual QA status stays traceable without cloud services",
                bullets=("K4 uses local OOXML checks", "No cloud vision is required"),
                layout_hint="data_summary",
            ),
            PlannedSlide(
                slide_id="slide_004",
                slide_type=SlideType.CONCLUSION,
                story_arc_stage=StoryArcStage.CLOSE,
                title="K5 prepares provenance for K6 without claiming Kimi-level",
                bullets=("Slide evidence is complete", "K6 remains the full end-to-end gate"),
                layout_hint="conclusion",
            ),
        ),
    )
    quality = improve_presentation_plan_render_quality(plan, profile=build_default_k3_quality_profile(template_id="business_clean"))
    provenance = build_source_to_slide_provenance(
        quality.render_plan,
        source_text=source_text,
        source_refs=(
            {
                "kind": "document",
                "source_id": "operator_memo_001",
                "title": "Operator memo",
                "role": "primary_source",
                "locator": "memo.md#executive-summary",
                "source_file_id": "file_operator_memo_001",
                "derived_content_id": "derived_text_001",
                "checksum_sha256": "abc123",
            },
        ),
    )
    render = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=provenance.plan,
            plan_snapshot_id="k5_source_to_slide_smoke_plan",
            render_mode="adaptive",
            template_id=quality.profile.template_id,
            artifact_filename="k5-source-to-slide-smoke.pptx",
        )
    )
    qa = run_visual_qa_runtime(
        VisualQARuntimeRequest(
            plan=provenance.plan,
            artifact_content=render.artifact_content,
            plan_snapshot_id="k5_source_to_slide_smoke_plan",
            render_mode="adaptive",
            template_id=quality.profile.template_id,
            artifact_filename="k5-source-to-slide-smoke.pptx",
        )
    )
    enriched_manifest = attach_k5_provenance_to_manifest(
        {
            "schema_version": "slides_provenance_manifest.v1",
            "workflow_id": "slides.provenance_manifest_runtime",
            "integrity": {"manifest_digest": "sha256:placeholder"},
        },
        provenance,
    )
    capabilities = build_k5_capabilities_report()
    validation_errors = validate_k5_source_to_slide_result(provenance)
    metadata = provenance.safe_metadata
    encoded_metadata = json.dumps(metadata, ensure_ascii=False, sort_keys=True).lower()
    errors: list[str] = list(validation_errors)

    pptx_slide_xml = _read_slide_xml(render.artifact_content)
    if metadata.get("checkpoint") != "K5":
        errors.append("K5 metadata checkpoint mismatch")
    if metadata.get("source_to_slide_provenance_supported") is not True:
        errors.append("K5 source-to-slide provenance not reported as supported")
    if provenance.coverage.coverage_status != "complete":
        errors.append("K5 provenance coverage is not complete")
    if len(provenance.slide_links) != len(provenance.plan.slides):
        errors.append("K5 slide link count must equal slide count")
    if not all(slide.citations for slide in provenance.plan.slides):
        errors.append("K5 enriched plan must attach citations to every slide")
    if "source_citation" not in pptx_slide_xml:
        errors.append("K5 rendered PPTX does not contain source citation footer shapes")
    if enriched_manifest.get("source_to_slide_provenance") != provenance.manifest_section:
        errors.append("K5 manifest attachment did not preserve the source-to-slide section")
    if "k5_source_to_slide_section_digest" not in enriched_manifest.get("integrity", {}):
        errors.append("K5 manifest attachment missing section digest")
    if qa.status not in {"passed", "needs_operator_review"}:
        errors.append(f"K5 provenance should not break K4 visual QA, got {qa.status}")
    if metadata.get("raw_source_text_stored") is not False:
        errors.append("K5 safe metadata must not store raw source text")
    if "customer churn dropped" in encoded_metadata:
        errors.append("K5 safe metadata contains raw source text")
    if capabilities.get("api_endpoint_added_by_k5") is not False:
        errors.append("K5 must not add API endpoint")
    if capabilities.get("db_schema_migration_added_by_k5") is not False:
        errors.append("K5 must not add DB schema migration")
    if capabilities.get("dependency_versions_changed_by_k5") is not False:
        errors.append("K5 must not change dependency versions")
    if capabilities.get("dockerfiles_changed_by_k5") is not False:
        errors.append("K5 must not change Dockerfiles")
    if capabilities.get("cloud_llm_added_by_k5") is not False or capabilities.get("cloud_vision_added_by_k5") is not False:
        errors.append("K5 must not add cloud LLM or cloud vision")
    if capabilities.get("k6_end_to_end_workflow_added_by_k5") is not False:
        errors.append("K5 must not claim K6 end-to-end workflow")
    if capabilities.get("kimi_level_claimed_by_k5") is not False:
        errors.append("K5 must not claim Kimi-level")
    if metadata.get("whole_project_kimi_level_supported") is not False:
        errors.append("K5 must not claim whole-project Kimi-level")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "source_to_slide_provenance_supported": metadata.get("source_to_slide_provenance_supported") is True,
        "slide_level_evidence_links_supported": metadata.get("slide_level_evidence_links_supported") is True,
        "fragment_digest_supported": metadata.get("fragment_digest_supported") is True,
        "bounded_excerpt_preview_supported": metadata.get("bounded_excerpt_preview_supported") is True,
        "plan_citation_enrichment_supported": metadata.get("plan_citation_enrichment_supported") is True,
        "manifest_section_supported": metadata.get("manifest_section_supported") is True,
        "coverage_report_supported": metadata.get("coverage_report_supported") is True,
        "safe_redaction_supported": metadata.get("safe_redaction_supported") is True,
        "coverage_status": provenance.coverage.coverage_status,
        "slide_count": len(provenance.plan.slides),
        "slide_evidence_link_count": len(provenance.slide_links),
        "source_count": len(provenance.sources),
        "fragment_count": len(provenance.fragments),
        "visual_qa_status": qa.status,
        "pptx_citation_footer_present": "source_citation" in pptx_slide_xml,
        "manifest_section_digest": provenance.manifest_section["integrity"]["section_digest"],
        "api_endpoint_added_by_k5": False,
        "db_schema_migration_added_by_k5": False,
        "frontend_runtime_changed_by_k5": False,
        "dependency_versions_changed_by_k5": False,
        "dockerfiles_changed_by_k5": False,
        "cloud_llm_added_by_k5": False,
        "cloud_vision_added_by_k5": False,
        "k6_end_to_end_workflow_added_by_k5": False,
        "kimi_level_claimed_by_k5": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }


def _read_slide_xml(pptx_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(pptx_bytes)) as archive:
        return "\n".join(
            archive.read(name).decode("utf-8", errors="replace")
            for name in sorted(archive.namelist())
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = static_errors + list(smoke.get("errors", []))
    return {
        "mode": "k5-source-to-slide-provenance-runtime",
        "phase": "K-phase",
        "checkpoint": "K5",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "k5_base_after_k4": EXPECTED_BASE_AFTER_K4,
        "runtime_changed_by_k5": True,
        "runtime_change_type": "source_to_slide_provenance_runtime_layer",
        "status": "ready" if not errors else "failed",
        "errors": errors,
        **{key: value for key, value in smoke.items() if key not in {"status", "errors"}},
        "next_recommended_step": "K6 — End-to-end Kimi-like workflow",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio K5 source-to-slide provenance runtime check.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"K5 source-to-slide provenance runtime: {report['status']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
