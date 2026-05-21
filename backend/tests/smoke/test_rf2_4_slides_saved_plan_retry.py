from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from backend.app.domain import Artifact, Presentation
from backend.app.services.slides_service import PresentationPlanSnapshotService, SlidesService
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage
from backend.app.services.slides_service.saved_plan_retry import SavedPlanRetryRequest, retry_saved_plan_with_lifecycle


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sample_plan() -> PresentationPlan:
    slides = (
        PlannedSlide(
            slide_id="rf2_4_001",
            slide_type=SlideType.TITLE,
            story_arc_stage=StoryArcStage.OPENING,
            title="RF2.4 Retry",
            bullets=("Saved plan", "Retry runtime"),
            layout_hint="title_slide",
        ),
        PlannedSlide(
            slide_id="rf2_4_002",
            slide_type=SlideType.CONTENT,
            story_arc_stage=StoryArcStage.ANALYSIS,
            title="Runtime path",
            bullets=("Load snapshot", "Register new artifact", "Persist new snapshot"),
            layout_hint="title_and_bullets",
        ),
        PlannedSlide(
            slide_id="rf2_4_003",
            slide_type=SlideType.CONCLUSION,
            story_arc_stage=StoryArcStage.CLOSE,
            title="Next",
            bullets=("RF2.5 render mode hardening",),
            layout_hint="conclusion",
        ),
    )
    return PresentationPlan(
        deck_title="RF2.4 Retry",
        deck_goal="Regenerate from saved plan snapshot with safe retry events.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=len(slides),
        story_arc=tuple(slide.story_arc_stage for slide in slides),
        slides=slides,
    )


class PresentationRepo:
    def __init__(self) -> None:
        self.presentation = Presentation(
            id="pres_rf2_4",
            session_id="ses_rf2_4",
            current_file_id=None,
            presentation_type="slides",
            title="RF2.4 Retry",
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
            id=f"art_rf2_4_{len(self.items) + 1}",
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
    snapshot_service.create_snapshot(
        presentation_id="pres_rf2_4",
        plan=sample_plan(),
        created_from_task_id="task_parent_rf2_4",
        change_summary="Saved parent plan.",
        snapshot_id="plansnap_parent_rf2_4",
    )
    return snapshot_service, artifact_service


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_saved_plan_retry_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf2_4_checker_reports_ready_saved_plan_retry_runtime() -> None:
    result = run_check("--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "slides-saved-plan-retry-runtime"
    assert payload["phase"] == "RF2"
    assert payload["checkpoint"] == "RF2.4"
    assert payload["status"] == "ready"
    assert payload["errors"] == []
    assert payload["runtime_changed_by_rf2_4"] is True
    assert payload["dependency_versions_changed_by_rf2_4"] is False
    assert payload["dockerfiles_changed_by_rf2_4"] is False
    assert payload["api_endpoint_added_by_rf2_4"] is False
    assert payload["db_schema_migration_added_by_rf2_4"] is False
    assert payload["queue_or_event_store_migration_added_by_rf2_4"] is False


def test_rf2_4_retry_loads_saved_snapshot_registers_new_artifact_and_new_snapshot() -> None:
    snapshot_service, artifact_service = build_services()
    result = retry_saved_plan_with_lifecycle(
        SavedPlanRetryRequest(
            saved_plan_snapshot_id="plansnap_parent_rf2_4",
            session_id="ses_rf2_4",
            retry_task_id="task_retry_rf2_4",
            parent_task_id="task_parent_rf2_4",
            presentation_id="pres_rf2_4",
            operator_instruction="Regenerate from the saved approved plan.",
            render_mode="adaptive",
            template_id="business_clean",
            new_plan_snapshot_id="plansnap_retry_rf2_4",
            artifact_filename="retry-deck.pptx",
        ),
        plan_snapshot_service=snapshot_service,
        artifact_service=artifact_service,
    )

    assert result.saved_plan_snapshot.id == "plansnap_parent_rf2_4"
    assert result.new_plan_snapshot.id == "plansnap_retry_rf2_4"
    assert result.new_plan_snapshot.created_from_task_id == "task_retry_rf2_4"
    assert result.artifact.filename == "retry-deck.pptx"
    assert artifact_service.items == [result.artifact]
    assert artifact_service.contents[0].startswith(b"PK")

    assert result.event_types == (
        "slides.retry.from_saved_plan.requested",
        "slides.retry.saved_plan_snapshot.loaded",
        "slides.retry.plan.validated",
        "slides.retry.render_mode.confirmed",
        "slides.retry.generation.started",
        "artifact.registered",
        "plan.snapshot.registered",
        "slides.retry.generation.completed",
    )

    assert result.safe_metadata["parent_task_id"] == "task_parent_rf2_4"
    assert result.safe_metadata["parent_plan_snapshot_id"] == "plansnap_parent_rf2_4"
    assert result.safe_metadata["new_plan_snapshot_id"] == "plansnap_retry_rf2_4"
    assert result.safe_metadata["new_artifact_id"] == result.artifact.id
    assert result.safe_metadata["retry_instruction_digest"].startswith("sha256:")
    assert result.safe_metadata["raw_operator_instruction_stored"] is False
    assert "Regenerate from the saved approved plan." not in json.dumps(result.safe_metadata)


def test_rf2_4_retry_events_use_safe_payload_only() -> None:
    snapshot_service, artifact_service = build_services()
    result = retry_saved_plan_with_lifecycle(
        SavedPlanRetryRequest(
            saved_plan_snapshot_id="plansnap_parent_rf2_4",
            session_id="ses_rf2_4",
            retry_task_id="task_retry_rf2_4",
            parent_task_id="task_parent_rf2_4",
            presentation_id="pres_rf2_4",
            operator_instruction="Use the saved plan but keep payload safe.",
            new_plan_snapshot_id="plansnap_retry_rf2_4",
        ),
        plan_snapshot_service=snapshot_service,
        artifact_service=artifact_service,
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
    forbidden_text = "Use the saved plan but keep payload safe."
    for event in result.events:
        assert event.workflow_id == "slides"
        assert event.task_id == "task_retry_rf2_4"
        assert event.session_id == "ses_rf2_4"
        assert set(event.safe_payload) <= allowed_keys
        assert "operator_instruction" not in event.safe_payload
        assert "secret" not in event.safe_payload
        assert "token" not in event.safe_payload
        assert forbidden_text not in json.dumps(event.safe_payload)


def test_rf2_4_slides_service_requires_lifecycle_dependencies_before_retry() -> None:
    service = SlidesService()
    with pytest.raises(ValueError, match="plan_snapshot_service"):
        service.retry_deck_from_saved_plan(
            saved_plan_snapshot_id="plansnap_parent_rf2_4",
            session_id="ses_rf2_4",
            retry_task_id="task_retry_rf2_4",
            parent_task_id="task_parent_rf2_4",
            presentation_id="pres_rf2_4",
            operator_instruction="Retry.",
        )

    snapshot_service, artifact_service = build_services()
    service = SlidesService(plan_snapshot_service=snapshot_service, artifact_service=artifact_service)
    result = service.retry_deck_from_saved_plan(
        saved_plan_snapshot_id="plansnap_parent_rf2_4",
        session_id="ses_rf2_4",
        retry_task_id="task_retry_rf2_4",
        parent_task_id="task_parent_rf2_4",
        presentation_id="pres_rf2_4",
        operator_instruction="Retry from service path.",
        new_plan_snapshot_id="plansnap_retry_service_rf2_4",
        artifact_filename="retry-service.pptx",
    )

    assert result.new_plan_snapshot.id == "plansnap_retry_service_rf2_4"
    assert result.artifact.filename == "retry-service.pptx"
    assert result.render_result.artifact_content.startswith(b"PK")


def test_rf2_4_rejects_missing_operator_instruction_and_same_task_id() -> None:
    snapshot_service, artifact_service = build_services()

    with pytest.raises(ValueError, match="operator_instruction"):
        retry_saved_plan_with_lifecycle(
            SavedPlanRetryRequest(
                saved_plan_snapshot_id="plansnap_parent_rf2_4",
                session_id="ses_rf2_4",
                retry_task_id="task_retry_rf2_4",
                parent_task_id="task_parent_rf2_4",
                presentation_id="pres_rf2_4",
                operator_instruction="",
            ),
            plan_snapshot_service=snapshot_service,
            artifact_service=artifact_service,
        )

    with pytest.raises(ValueError, match="retry_task_id to differ"):
        retry_saved_plan_with_lifecycle(
            SavedPlanRetryRequest(
                saved_plan_snapshot_id="plansnap_parent_rf2_4",
                session_id="ses_rf2_4",
                retry_task_id="task_same",
                parent_task_id="task_same",
                presentation_id="pres_rf2_4",
                operator_instruction="Retry.",
            ),
            plan_snapshot_service=snapshot_service,
            artifact_service=artifact_service,
        )


def test_rf2_4_rejects_missing_or_mismatched_saved_snapshot() -> None:
    snapshot_service, artifact_service = build_services()

    with pytest.raises(ValueError, match="not found"):
        retry_saved_plan_with_lifecycle(
            SavedPlanRetryRequest(
                saved_plan_snapshot_id="missing_snapshot",
                session_id="ses_rf2_4",
                retry_task_id="task_retry_rf2_4",
                parent_task_id="task_parent_rf2_4",
                presentation_id="pres_rf2_4",
                operator_instruction="Retry.",
            ),
            plan_snapshot_service=snapshot_service,
            artifact_service=artifact_service,
        )

    with pytest.raises(ValueError, match="presentation_id"):
        retry_saved_plan_with_lifecycle(
            SavedPlanRetryRequest(
                saved_plan_snapshot_id="plansnap_parent_rf2_4",
                session_id="ses_rf2_4",
                retry_task_id="task_retry_rf2_4",
                parent_task_id="task_parent_rf2_4",
                presentation_id="other_presentation",
                operator_instruction="Retry.",
            ),
            plan_snapshot_service=snapshot_service,
            artifact_service=artifact_service,
        )


def test_rf2_4_checker_smoke_preserves_no_kimi_overclaim() -> None:
    result = run_check("--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    smoke = payload["runtime_smoke"]

    assert smoke["saved_plan_retry_supported"] is True
    assert smoke["saved_plan_snapshot_loaded"] is True
    assert smoke["new_plan_snapshot_persisted"] is True
    assert smoke["new_artifact_registered"] is True
    assert smoke["retry_event_order_valid"] is True
    assert smoke["retry_parent_links_present"] is True
    assert smoke["safe_payload_only"] is True
    assert smoke["raw_operator_instruction_stored"] is False
    assert smoke["retry_instruction_digest_present"] is True
    assert smoke["kimi_grade_supported"] is False
    assert smoke["product_grade_supported"] is False
    assert smoke["whole_project_kimi_level_supported"] is False


def test_rf2_4_production_readiness_gate_mentions_saved_plan_retry() -> None:
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "Slides saved-plan retry runtime" in gate
    assert "scripts/kw_slides_saved_plan_retry_check.py" in gate
    assert "docs/codex/SLIDES_SAVED_PLAN_RETRY_RUNTIME.md" in gate
    assert "backend/tests/smoke/test_rf2_4_slides_saved_plan_retry.py" in gate
