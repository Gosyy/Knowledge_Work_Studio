from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from backend.app.domain import Artifact, Presentation
from backend.app.services.slides_service import PresentationPlanSnapshotService, SlidesService
from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, render_approved_plan_to_pptx
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage
from backend.app.services.slides_service.render_mode_runtime import RenderModeRuntimeRequest, resolve_render_mode_runtime


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sample_plan() -> PresentationPlan:
    slides = (
        PlannedSlide(
            slide_id="rf2_5_001",
            slide_type=SlideType.TITLE,
            story_arc_stage=StoryArcStage.OPENING,
            title="RF2.5 Render Modes",
            bullets=("Adaptive", "Template"),
            layout_hint="title_slide",
        ),
        PlannedSlide(
            slide_id="rf2_5_002",
            slide_type=SlideType.CONTENT,
            story_arc_stage=StoryArcStage.ANALYSIS,
            title="Local policy",
            bullets=("Bundled templates only", "No external downloads", "Safe metadata"),
            layout_hint="title_and_bullets",
        ),
        PlannedSlide(
            slide_id="rf2_5_003",
            slide_type=SlideType.CONCLUSION,
            story_arc_stage=StoryArcStage.CLOSE,
            title="Next",
            bullets=("RF2.6 provenance manifest emission",),
            layout_hint="conclusion",
        ),
    )
    return PresentationPlan(
        deck_title="RF2.5 Render Modes",
        deck_goal="Harden adaptive/template render mode runtime behavior.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=len(slides),
        story_arc=tuple(slide.story_arc_stage for slide in slides),
        slides=slides,
    )


class PresentationRepo:
    def __init__(self) -> None:
        self.presentation = Presentation(
            id="pres_rf2_5",
            session_id="ses_rf2_5",
            current_file_id=None,
            presentation_type="slides",
            title="RF2.5 Render Modes",
        )

    def create(self, presentation: Presentation) -> Presentation:
        self.presentation = presentation
        return presentation

    def get(self, presentation_id: str) -> Presentation | None:
        return self.presentation if presentation_id == self.presentation.id else None

    def list_by_session(self, session_id: str) -> list[Presentation]:
        return [self.presentation] if session_id == self.presentation.session_id else []


class PresentationVersionRepo:
    def create(self, presentation_version: Any) -> Any:
        return presentation_version

    def list_by_presentation(self, presentation_id: str) -> list[Any]:
        return []


class SnapshotRepo:
    def __init__(self) -> None:
        self.items: list[Any] = []

    def create(self, snapshot: Any) -> Any:
        self.items.append(snapshot)
        return snapshot

    def get(self, snapshot_id: str) -> Any | None:
        return next((item for item in self.items if item.id == snapshot_id), None)

    def list_by_presentation(self, presentation_id: str) -> list[Any]:
        return [item for item in self.items if item.presentation_id == presentation_id]

    def get_latest_for_presentation(self, presentation_id: str) -> Any | None:
        matches = self.list_by_presentation(presentation_id)
        return matches[-1] if matches else None

    def get_by_version(self, presentation_version_id: str) -> Any | None:
        return next((item for item in self.items if item.presentation_version_id == presentation_version_id), None)


class ArtifactService:
    def __init__(self) -> None:
        self.items: list[Artifact] = []

    def create_artifact_from_bytes(
        self,
        *,
        session_id: str,
        task_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Artifact:
        artifact = Artifact(
            id=f"art_rf2_5_{len(self.items) + 1}",
            session_id=session_id,
            task_id=task_id,
            filename=filename,
            content_type=content_type,
            storage_backend="memory",
            storage_key=f"memory/{filename}",
            storage_uri=f"memory://{filename}",
            size_bytes=len(content),
        )
        self.items.append(artifact)
        return artifact


def build_service() -> SlidesService:
    snapshot_service = PresentationPlanSnapshotService(
        snapshots=SnapshotRepo(),
        presentations=PresentationRepo(),
        presentation_versions=PresentationVersionRepo(),
    )
    snapshot_service.create_snapshot(
        presentation_id="pres_rf2_5",
        plan=sample_plan(),
        created_from_task_id="task_parent_rf2_5",
        change_summary="Saved parent plan.",
        snapshot_id="plansnap_parent_rf2_5",
    )
    return SlidesService(plan_snapshot_service=snapshot_service, artifact_service=ArtifactService())


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_render_mode_runtime_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf2_5_checker_reports_ready_runtime_hardening() -> None:
    result = run_check("--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "slides-render-mode-runtime-hardening"
    assert payload["phase"] == "RF2"
    assert payload["checkpoint"] == "RF2.5"
    assert payload["status"] == "ready"
    assert payload["errors"] == []
    assert payload["runtime_changed_by_rf2_5"] is True
    assert payload["runtime_change_type"] == "adaptive_template_local_render_mode_runtime_hardening"
    assert payload["dependency_versions_changed_by_rf2_5"] is False
    assert payload["dockerfiles_changed_by_rf2_5"] is False
    assert payload["api_endpoint_added_by_rf2_5"] is False
    assert payload["db_schema_migration_added_by_rf2_5"] is False
    assert payload["provenance_manifest_emitted_by_rf2_5"] is False
    assert payload["visual_qa_runtime_added_by_rf2_5"] is False


def test_rf2_5_adaptive_mode_resolves_local_default_template() -> None:
    result = resolve_render_mode_runtime(
        RenderModeRuntimeRequest(
            render_mode="adaptive",
            template_id="",
            plan_snapshot_id="plansnap_adaptive_rf2_5",
            approved_plan=True,
        )
    )

    assert result.render_mode == "adaptive"
    assert result.resolved_template_id == "business_clean"
    assert result.template_source == "local_builtin_registry"
    assert result.template_locked is False
    assert result.adaptive_layout_selection_enabled is True
    assert result.external_template_download_allowed is False
    assert result.network_required is False


def test_rf2_5_template_mode_requires_explicit_local_template_id() -> None:
    with pytest.raises(ValueError, match="template_id"):
        resolve_render_mode_runtime(
            RenderModeRuntimeRequest(
                render_mode="template",
                template_id="",
                plan_snapshot_id="plansnap_template_rf2_5",
                approved_plan=True,
            )
        )

    result = resolve_render_mode_runtime(
        RenderModeRuntimeRequest(
            render_mode="template",
            template_id="business_clean",
            plan_snapshot_id="plansnap_template_rf2_5",
            approved_plan=True,
        )
    )

    assert result.resolved_template_id == "business_clean"
    assert result.template_id_required is True
    assert result.template_locked is True
    assert result.adaptive_layout_selection_enabled is False


def test_rf2_5_rejects_external_path_and_unknown_template_references() -> None:
    for template_id in (
        "https://templates.example.com/business_clean.pptx",
        "s3://bucket/business_clean.pptx",
        "../business_clean",
        "nested/business_clean",
        "unknown_template_id",
    ):
        with pytest.raises(ValueError):
            resolve_render_mode_runtime(
                RenderModeRuntimeRequest(
                    render_mode="template",
                    template_id=template_id,
                    plan_snapshot_id="plansnap_bad_template_rf2_5",
                    approved_plan=True,
                )
            )


def test_rf2_5_approved_plan_render_metadata_contains_runtime_policy() -> None:
    adaptive = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=sample_plan(),
            plan_snapshot_id="plansnap_approved_adaptive_rf2_5",
            approval_status="approved",
            render_mode="adaptive",
            template_id="",
            artifact_filename="rf2-5-adaptive.pptx",
        )
    )
    template = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=sample_plan(),
            plan_snapshot_id="plansnap_approved_template_rf2_5",
            approval_status="approved",
            render_mode="template",
            template_id="business_clean",
            artifact_filename="rf2-5-template.pptx",
        )
    )

    for result in (adaptive, template):
        assert result.artifact_content.startswith(b"PK")
        assert result.safe_metadata["render_mode_runtime_hardened"] is True
        assert result.safe_metadata["template_source"] == "local_builtin_registry"
        assert result.safe_metadata["external_template_download_allowed"] is False
        assert result.safe_metadata["local_template_registry_enforced"] is True
        assert result.safe_metadata["runtime_changed_by_rf2_5"] is True
        assert result.safe_metadata["kimi_grade_supported"] is False
        assert result.safe_metadata["whole_project_kimi_level_supported"] is False

    assert adaptive.template_id == "business_clean"
    assert adaptive.safe_metadata["template_locked"] is False
    assert template.safe_metadata["template_locked"] is True


def test_rf2_5_retry_metadata_preserves_render_mode_policy_without_raw_instruction() -> None:
    service = build_service()
    result = service.retry_deck_from_saved_plan(
        saved_plan_snapshot_id="plansnap_parent_rf2_5",
        session_id="ses_rf2_5",
        retry_task_id="task_retry_rf2_5",
        parent_task_id="task_parent_rf2_5",
        presentation_id="pres_rf2_5",
        operator_instruction="Retry RF2.5 using saved plan.",
        render_mode="template",
        template_id="business_clean",
        new_plan_snapshot_id="plansnap_retry_rf2_5",
        artifact_filename="rf2-5-retry.pptx",
    )

    assert result.render_result.artifact_content.startswith(b"PK")
    assert result.safe_metadata["render_mode_runtime_hardened"] is True
    assert result.safe_metadata["template_source"] == "local_builtin_registry"
    assert result.safe_metadata["template_locked"] is True
    assert result.safe_metadata["external_template_download_allowed"] is False
    assert result.safe_metadata["raw_operator_instruction_stored"] is False
    assert "Retry RF2.5" not in json.dumps(result.safe_metadata)


def test_rf2_5_slides_service_exposes_render_mode_runtime_validation() -> None:
    service = SlidesService()
    result = service.validate_render_mode_runtime(
        render_mode="adaptive",
        template_id="",
        plan_snapshot_id="plansnap_service_rf2_5",
        approved_plan=True,
    )

    assert result.render_mode == "adaptive"
    assert result.resolved_template_id == "business_clean"
    assert result.external_template_download_allowed is False


def test_rf2_5_production_readiness_gate_mentions_render_mode_runtime() -> None:
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "Slides render mode runtime hardening" in gate
    assert "scripts/kw_slides_render_mode_runtime_check.py" in gate
    assert "docs/codex/SLIDES_RENDER_MODE_RUNTIME_HARDENING.md" in gate
    assert "backend/tests/smoke/test_rf2_5_slides_render_mode_runtime.py" in gate
