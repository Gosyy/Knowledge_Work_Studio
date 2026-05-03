from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from backend.app.services.slides_service import ApprovedPlanRenderRequest, SlidesService
from backend.app.services.slides_service.approved_plan import render_approved_plan_to_pptx
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sample_plan() -> PresentationPlan:
    slides = (
        PlannedSlide(
            slide_id="approved_001",
            slide_type=SlideType.TITLE,
            story_arc_stage=StoryArcStage.OPENING,
            title="Approved Plan Runtime",
            bullets=("Operator reviewed outline", "Deterministic PPTX path"),
            layout_hint="title_slide",
        ),
        PlannedSlide(
            slide_id="approved_002",
            slide_type=SlideType.CONTENT,
            story_arc_stage=StoryArcStage.ANALYSIS,
            title="Runtime Contract",
            bullets=("Requires explicit approval", "Preserves safe metadata", "Avoids network calls"),
            layout_hint="title_and_bullets",
        ),
        PlannedSlide(
            slide_id="approved_003",
            slide_type=SlideType.CONCLUSION,
            story_arc_stage=StoryArcStage.CLOSE,
            title="Next Step",
            bullets=("Persist artifact", "Link plan snapshot", "Emit task events"),
            layout_hint="conclusion",
        ),
    )
    return PresentationPlan(
        deck_title="Approved Plan Runtime",
        deck_goal="Render an approved plan into deterministic PPTX bytes.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=len(slides),
        story_arc=tuple(slide.story_arc_stage for slide in slides),
        slides=slides,
    )


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_approved_plan_runtime_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf2_2_checker_reports_ready_additive_runtime_path() -> None:
    result = run_check("--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "slides-approved-plan-runtime"
    assert payload["phase"] == "RF2"
    assert payload["checkpoint"] == "RF2.2"
    assert payload["network_required"] is False
    assert payload["runtime_changed_by_rf2_2"] is True
    assert payload["runtime_change_type"] == "additive_backend_service_path"
    assert payload["dependency_versions_changed_by_rf2_2"] is False
    assert payload["dockerfiles_changed_by_rf2_2"] is False
    assert payload["frontend_runtime_changed_by_rf2_2"] is False
    assert payload["api_endpoint_added_by_rf2_2"] is False
    assert payload["persistence_added_by_rf2_2"] is False
    assert payload["provenance_manifest_emitted_by_rf2_2"] is False
    assert payload["status"] == "ready"
    assert payload["errors"] == []


def test_rf2_2_renders_approved_plan_to_deterministic_pptx() -> None:
    plan = sample_plan()
    request = ApprovedPlanRenderRequest(
        plan=plan,
        plan_snapshot_id="plansnap_test",
        approval_status="approved",
        render_mode="adaptive",
        template_id="business_clean",
        artifact_filename="approved-plan-test.pptx",
    )

    first = render_approved_plan_to_pptx(request)
    second = render_approved_plan_to_pptx(request)

    assert first.artifact_content == second.artifact_content
    assert first.checksum_sha256 == second.checksum_sha256
    assert first.content_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    assert first.artifact_filename == "approved-plan-test.pptx"
    assert first.size_bytes == len(first.artifact_content)
    assert first.slide_count == 3
    assert first.render_mode == "adaptive"
    assert first.template_id == "business_clean"
    assert first.artifact_content.startswith(b"PK")
    assert first.safe_metadata["network_required"] is False
    assert first.safe_metadata["kimi_grade_supported"] is False
    assert first.safe_metadata["whole_project_kimi_level_supported"] is False

    with zipfile.ZipFile(BytesIO(first.artifact_content), "r") as pptx:
        names = set(pptx.namelist())

    assert "[Content_Types].xml" in names
    assert "ppt/presentation.xml" in names
    assert "ppt/slides/slide1.xml" in names


def test_rf2_2_service_exposes_approved_plan_generation_method() -> None:
    service = SlidesService()
    result = service.generate_deck_from_approved_plan(
        sample_plan(),
        plan_snapshot_id="plansnap_service",
        approval_status="approved",
        render_mode="template",
        template_id="business_clean",
        artifact_filename="service-approved-plan.pptx",
    )

    assert result.artifact_filename == "service-approved-plan.pptx"
    assert result.render_mode == "template"
    assert result.template_id == "business_clean"
    assert result.slide_count == 3
    assert result.artifact_content.startswith(b"PK")


def test_rf2_2_rejects_unapproved_or_unsafe_requests() -> None:
    plan = sample_plan()

    with pytest.raises(ValueError, match="approval_status"):
        render_approved_plan_to_pptx(
            ApprovedPlanRenderRequest(
                plan=plan,
                plan_snapshot_id="plansnap_unapproved",
                approval_status="draft",
            )
        )

    with pytest.raises(ValueError, match="template_id"):
        render_approved_plan_to_pptx(
            ApprovedPlanRenderRequest(
                plan=plan,
                plan_snapshot_id="plansnap_template",
                approval_status="approved",
                render_mode="template",
                template_id="",
            )
        )

    with pytest.raises(ValueError, match="safe local filename"):
        render_approved_plan_to_pptx(
            ApprovedPlanRenderRequest(
                plan=plan,
                plan_snapshot_id="plansnap_unsafe",
                approval_status="approved",
                artifact_filename="../bad.pptx",
            )
        )


def test_rf2_2_checker_smoke_preserves_no_kimi_overclaim() -> None:
    result = run_check("--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    smoke = payload["runtime_smoke"]

    assert smoke["approved_plan_runtime_supported"] is True
    assert smoke["approved_plan_runtime_scope"] == "minimal_backend_runtime_bridge"
    assert smoke["kimi_grade_supported"] is False
    assert smoke["product_grade_supported"] is False
    assert smoke["whole_project_kimi_level_supported"] is False
    assert smoke["payload_starts_with_pk"] is True
    assert smoke["deterministic_bytes"] is True
    assert smoke["rejected_unapproved_plan"] is True
    assert smoke["rejected_template_mode_without_template_id"] is True


def test_rf2_2_production_readiness_gate_mentions_approved_plan_runtime() -> None:
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "Slides approved-plan deterministic PPTX runtime" in gate
    assert "scripts/kw_slides_approved_plan_runtime_check.py" in gate
    assert "docs/codex/SLIDES_APPROVED_PLAN_RUNTIME.md" in gate
    assert "backend/tests/smoke/test_rf2_2_slides_approved_plan_runtime.py" in gate
