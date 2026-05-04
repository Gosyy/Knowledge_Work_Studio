from __future__ import annotations

import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from backend.app.services.k_phase.renderer_quality import build_default_k3_quality_profile, improve_presentation_plan_render_quality
from backend.app.services.k_phase.source_to_slide_provenance import (
    attach_k5_provenance_to_manifest,
    build_k5_capabilities_report,
    build_source_to_slide_provenance,
    validate_k5_source_to_slide_result,
)
from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, render_approved_plan_to_pptx
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_k5_source_to_slide_provenance_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def source_text() -> str:
    return (
        "Offline planning adopted approval gates before rendering. "
        "Renderer quality was improved through deterministic density controls. "
        "Visual QA now inspects local PPTX OOXML without cloud services. "
        "Source-to-slide provenance is required before the K6 end-to-end workflow."
    )


def base_plan() -> PresentationPlan:
    return PresentationPlan(
        deck_title="K5 provenance runtime",
        deck_goal="Trace every slide to a bounded source fragment.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=3,
        story_arc=(StoryArcStage.OPENING, StoryArcStage.ANALYSIS, StoryArcStage.CLOSE),
        slides=(
            PlannedSlide(
                slide_id="slide_001",
                slide_type=SlideType.TITLE,
                story_arc_stage=StoryArcStage.OPENING,
                title="Approval gates make the source path visible",
                bullets=("Plan before render", "Evidence before export"),
                layout_hint="title_with_visual",
            ),
            PlannedSlide(
                slide_id="slide_002",
                slide_type=SlideType.CONTENT,
                story_arc_stage=StoryArcStage.ANALYSIS,
                title="Deterministic renderer quality keeps provenance stable",
                bullets=("Density controls are local", "Layout decisions are metadata-backed"),
                layout_hint="content_with_visual",
            ),
            PlannedSlide(
                slide_id="slide_003",
                slide_type=SlideType.CONCLUSION,
                story_arc_stage=StoryArcStage.CLOSE,
                title="K5 prepares the K6 workflow without claiming it",
                bullets=("Every slide has evidence", "Kimi-level remains gated by K6"),
                layout_hint="conclusion",
            ),
        ),
    )


def k5_result():
    quality = improve_presentation_plan_render_quality(base_plan(), profile=build_default_k3_quality_profile(template_id="business_clean"))
    return build_source_to_slide_provenance(
        quality.render_plan,
        source_text=source_text(),
        source_refs=(
            {
                "kind": "document",
                "source_id": "memo_001",
                "title": "Architecture memo",
                "role": "primary_source",
                "locator": "memo.md#k-phase",
                "source_file_id": "file_memo_001",
                "derived_content_id": "derived_memo_text_001",
                "checksum_sha256": "abc123",
            },
        ),
    )


def test_k5_checker_reports_ready_without_scope_escape() -> None:
    result = run_check("--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "K5"
    assert payload["status"] == "ready"
    assert payload["runtime_changed_by_k5"] is True
    assert payload["source_to_slide_provenance_supported"] is True
    assert payload["coverage_status"] == "complete"
    assert payload["api_endpoint_added_by_k5"] is False
    assert payload["db_schema_migration_added_by_k5"] is False
    assert payload["frontend_runtime_changed_by_k5"] is False
    assert payload["dependency_versions_changed_by_k5"] is False
    assert payload["dockerfiles_changed_by_k5"] is False
    assert payload["cloud_llm_added_by_k5"] is False
    assert payload["cloud_vision_added_by_k5"] is False
    assert payload["k6_end_to_end_workflow_added_by_k5"] is False
    assert payload["kimi_level_claimed_by_k5"] is False
    assert payload["whole_project_kimi_level_supported"] is False


def test_k5_enriches_every_slide_with_citation_and_safe_metadata() -> None:
    result = k5_result()
    errors = validate_k5_source_to_slide_result(result)
    assert errors == []
    assert result.coverage.coverage_status == "complete"
    assert len(result.slide_links) == len(result.plan.slides)
    assert all(slide.citations for slide in result.plan.slides)
    assert all(slide.source_notes for slide in result.plan.slides)
    assert result.safe_metadata["raw_source_text_stored"] is False
    assert result.safe_metadata["network_required"] is False
    assert "offline planning adopted" not in json.dumps(result.safe_metadata, ensure_ascii=False).lower()


def test_k5_manifest_section_has_digest_and_can_attach_to_rf_manifest_copy() -> None:
    result = k5_result()
    section = result.manifest_section
    assert section["checkpoint"] == "K5"
    assert section["coverage"]["coverage_status"] == "complete"
    assert section["integrity"]["section_digest"].startswith("sha256:")
    attached = attach_k5_provenance_to_manifest(
        {
            "schema_version": "slides_provenance_manifest.v1",
            "workflow_id": "slides.provenance_manifest_runtime",
            "integrity": {"manifest_digest": "sha256:existing"},
        },
        result,
    )
    assert attached["source_to_slide_provenance"] == section
    assert attached["integrity"]["manifest_digest"] == "sha256:existing"
    assert attached["integrity"]["k5_source_to_slide_section_digest"] == section["integrity"]["section_digest"]


def test_k5_rendered_pptx_contains_source_citation_footer_shapes() -> None:
    result = k5_result()
    render = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=result.plan,
            plan_snapshot_id="k5_test_plan",
            render_mode="adaptive",
            template_id="business_clean",
            artifact_filename="k5-test.pptx",
        )
    )
    with zipfile.ZipFile(io.BytesIO(render.artifact_content)) as archive:
        slide_xml = "\n".join(
            archive.read(name).decode("utf-8", errors="replace")
            for name in sorted(archive.namelist())
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
    assert "source_citation" in slide_xml
    assert "document/memo_001" in slide_xml


def test_k5_capabilities_keep_k6_and_kimi_level_separate() -> None:
    capabilities = build_k5_capabilities_report()
    assert capabilities["source_to_slide_provenance_supported"] is True
    assert capabilities["k6_end_to_end_workflow_added_by_k5"] is False
    assert capabilities["api_endpoint_added_by_k5"] is False
    assert capabilities["db_schema_migration_added_by_k5"] is False
    assert capabilities["cloud_llm_added_by_k5"] is False
    assert capabilities["cloud_vision_added_by_k5"] is False
    assert capabilities["kimi_level_claimed_by_k5"] is False
    assert capabilities["whole_project_kimi_level_supported"] is False
