from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from backend.app.domain import Artifact, Presentation
from backend.app.services.slides_service import PresentationPlanSnapshotService, SlidesService
from backend.app.services.slides_service.approved_plan_lifecycle import ApprovedPlanLifecycleRequest, render_approved_plan_with_lifecycle
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sample_plan() -> PresentationPlan:
    slides = (
        PlannedSlide(
            slide_id="rf2_3_001",
            slide_type=SlideType.TITLE,
            story_arc_stage=StoryArcStage.OPENING,
            title="RF2.3 Lifecycle",
            bullets=("Approved plan", "Snapshot and events"),
            layout_hint="title_slide",
        ),
        PlannedSlide(
            slide_id="rf2_3_002",
            slide_type=SlideType.CONTENT,
            story_arc_stage=StoryArcStage.ANALYSIS,
            title="Runtime wiring",
            bullets=("Persist snapshot", "Register artifact", "Emit safe events"),
            layout_hint="title_and_bullets",
        ),
        PlannedSlide(
            slide_id="rf2_3_003",
            slide_type=SlideType.CONCLUSION,
            story_arc_stage=StoryArcStage.CLOSE,
            title="Next",
            bullets=("RF2.4 saved-plan retry",),
            layout_hint="conclusion",
        ),
    )
    return PresentationPlan(
        deck_title="RF2.3 Lifecycle",
        deck_goal="Wire approved plan runtime into snapshot and event lifecycle.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=len(slides),
        story_arc=tuple(slide.story_arc_stage for slide in slides),
        slides=slides,
    )


class PresentationRepo:
    def __init__(self) -> None:
        self.presentation = Presentation(
            id="pres_rf2_3",
            session_id="ses_rf2_3",
            current_file_id=None,
            presentation_type="slides",
            title="RF2.3 Lifecycle",
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
        self.contents: list[bytes] = []

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
            id=f"art_rf2_3_{len(self.items) + 1}",
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
        self.contents.append(content)
        return artifact


def build_services() -> tuple[PresentationPlanSnapshotService, ArtifactService]:
    artifact_service = ArtifactService()
    snapshot_service = PresentationPlanSnapshotService(
        snapshots=SnapshotRepo(),
        presentations=PresentationRepo(),
        presentation_versions=PresentationVersionRepo(),
    )
    return snapshot_service, artifact_service


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_approved_plan_lifecycle_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf2_3_checker_reports_ready_runtime_lifecycle_wiring() -> None:
    result = run_check("--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "slides-approved-plan-lifecycle-runtime"
    assert payload["phase"] == "RF2"
    assert payload["checkpoint"] == "RF2.3"
    assert payload["status"] == "ready"
    assert payload["errors"] == []
    assert payload["runtime_changed_by_rf2_3"] is True
    assert payload["dependency_versions_changed_by_rf2_3"] is False
    assert payload["dockerfiles_changed_by_rf2_3"] is False
    assert payload["api_endpoint_added_by_rf2_3"] is False
    assert payload["db_schema_migration_added_by_rf2_3"] is False
    assert payload["saved_plan_retry_implemented_by_rf2_3"] is False


def test_rf2_3_lifecycle_persists_snapshot_registers_artifact_and_emits_safe_events() -> None:
    snapshot_service, artifact_service = build_services()
    result = render_approved_plan_with_lifecycle(
        ApprovedPlanLifecycleRequest(
            plan=sample_plan(),
            session_id="ses_rf2_3",
            task_id="task_rf2_3",
            presentation_id="pres_rf2_3",
            plan_snapshot_id="plansnap_rf2_3",
            render_mode="adaptive",
            template_id="business_clean",
            artifact_filename="rf2-3-approved-plan.pptx",
        ),
        plan_snapshot_service=snapshot_service,
        artifact_service=artifact_service,
    )

    assert result.plan_snapshot.id == "plansnap_rf2_3"
    assert result.plan_snapshot.presentation_id == "pres_rf2_3"
    assert result.plan_snapshot.created_from_task_id == "task_rf2_3"
    assert artifact_service.items == [result.artifact]
    assert artifact_service.contents[0].startswith(b"PK")
    assert result.artifact.filename == "rf2-3-approved-plan.pptx"

    assert result.event_types == (
        "slides.plan.approved",
        "slides.render_mode.selected",
        "slides.generation.started",
        "artifact.registered",
        "plan.snapshot.registered",
        "slides.generation.completed",
    )

    allowed_keys = {
        "plan_snapshot_id",
        "presentation_id",
        "presentation_version_id",
        "render_mode",
        "artifact_id",
        "artifact_filename",
        "retry_of_task_id",
        "change_summary",
        "error_code",
    }
    for event in result.events:
        assert event.workflow_id == "slides"
        assert event.task_id == "task_rf2_3"
        assert event.session_id == "ses_rf2_3"
        assert set(event.safe_payload) <= allowed_keys
        assert "secret" not in event.safe_payload
        assert "token" not in event.safe_payload
        assert "database_url" not in event.safe_payload

    assert result.safe_metadata["plan_snapshot_persisted"] is True
    assert result.safe_metadata["artifact_registered"] is True
    assert result.safe_metadata["kimi_grade_supported"] is False
    assert result.safe_metadata["whole_project_kimi_level_supported"] is False


def test_rf2_3_slides_service_requires_lifecycle_dependencies_before_runtime_wiring() -> None:
    service = SlidesService()
    with pytest.raises(ValueError, match="plan_snapshot_service"):
        service.generate_deck_from_approved_plan_with_lifecycle(
            sample_plan(),
            session_id="ses_rf2_3",
            task_id="task_rf2_3",
            presentation_id="pres_rf2_3",
        )

    snapshot_service, artifact_service = build_services()
    service = SlidesService(plan_snapshot_service=snapshot_service, artifact_service=artifact_service)
    result = service.generate_deck_from_approved_plan_with_lifecycle(
        sample_plan(),
        session_id="ses_rf2_3",
        task_id="task_rf2_3",
        presentation_id="pres_rf2_3",
        plan_snapshot_id="plansnap_via_service",
        artifact_filename="service-lifecycle.pptx",
    )

    assert result.plan_snapshot.id == "plansnap_via_service"
    assert result.artifact.filename == "service-lifecycle.pptx"
    assert result.render_result.artifact_content.startswith(b"PK")


def test_rf2_3_rejects_unapproved_lifecycle_request() -> None:
    snapshot_service, artifact_service = build_services()

    with pytest.raises(ValueError, match="approval_status"):
        render_approved_plan_with_lifecycle(
            ApprovedPlanLifecycleRequest(
                plan=sample_plan(),
                session_id="ses_rf2_3",
                task_id="task_rf2_3",
                presentation_id="pres_rf2_3",
                approval_status="draft",
            ),
            plan_snapshot_service=snapshot_service,
            artifact_service=artifact_service,
        )


def test_rf2_3_checker_smoke_preserves_no_kimi_overclaim() -> None:
    result = run_check("--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    smoke = payload["runtime_smoke"]

    assert smoke["approved_plan_lifecycle_supported"] is True
    assert smoke["plan_snapshot_persisted"] is True
    assert smoke["artifact_registered"] is True
    assert smoke["event_order_valid"] is True
    assert smoke["safe_payload_only"] is True
    assert smoke["kimi_grade_supported"] is False
    assert smoke["product_grade_supported"] is False
    assert smoke["whole_project_kimi_level_supported"] is False


def test_rf2_3_production_readiness_gate_mentions_lifecycle_runtime() -> None:
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "Slides approved-plan lifecycle runtime" in gate
    assert "scripts/kw_slides_approved_plan_lifecycle_check.py" in gate
    assert "docs/codex/SLIDES_APPROVED_PLAN_LIFECYCLE_RUNTIME.md" in gate
    assert "backend/tests/smoke/test_rf2_3_slides_approved_plan_lifecycle.py" in gate
