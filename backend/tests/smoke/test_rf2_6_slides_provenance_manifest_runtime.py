from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from backend.app.domain import Artifact, Presentation
from backend.app.services.slides_service import PresentationPlanSnapshotService, SlidesService
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage
from backend.app.services.slides_service.provenance_manifest_runtime import (
    PROVENANCE_MANIFEST_CONTENT_TYPE,
    build_generation_provenance_manifest,
    build_retry_provenance_manifest,
    verify_manifest_digest,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sample_plan() -> PresentationPlan:
    slides = (
        PlannedSlide(
            slide_id="rf2_6_001",
            slide_type=SlideType.TITLE,
            story_arc_stage=StoryArcStage.OPENING,
            title="RF2.6 Provenance",
            bullets=("PPTX artifact", "Manifest artifact"),
            layout_hint="title_slide",
        ),
        PlannedSlide(
            slide_id="rf2_6_002",
            slide_type=SlideType.CONTENT,
            story_arc_stage=StoryArcStage.ANALYSIS,
            title="Runtime links",
            bullets=("Plan snapshot", "Render mode", "Event refs"),
            layout_hint="title_and_bullets",
        ),
        PlannedSlide(
            slide_id="rf2_6_003",
            slide_type=SlideType.CONCLUSION,
            story_arc_stage=StoryArcStage.CLOSE,
            title="Next",
            bullets=("RF2.7 runtime closure",),
            layout_hint="conclusion",
        ),
    )
    return PresentationPlan(
        deck_title="RF2.6 Provenance",
        deck_goal="Emit downloadable provenance manifests for generated and retry decks.",
        audience="operator",
        tone="clear_professional",
        target_slide_count=len(slides),
        story_arc=tuple(slide.story_arc_stage for slide in slides),
        slides=slides,
    )


class PresentationRepo:
    def __init__(self) -> None:
        self.presentation = Presentation(
            id="pres_rf2_6",
            session_id="ses_rf2_6",
            current_file_id=None,
            presentation_type="slides",
            title="RF2.6 Provenance",
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
            id=f"art_rf2_6_{len(self.items) + 1}",
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


def build_service() -> tuple[SlidesService, ArtifactService]:
    artifact_service = ArtifactService()
    snapshot_service = PresentationPlanSnapshotService(
        snapshots=SnapshotRepo(),
        presentations=PresentationRepo(),
        presentation_versions=PresentationVersionRepo(),
    )
    return SlidesService(plan_snapshot_service=snapshot_service, artifact_service=artifact_service), artifact_service


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_provenance_manifest_runtime_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf2_6_checker_reports_ready_runtime_manifest_emission() -> None:
    result = run_check("--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "slides-provenance-manifest-runtime"
    assert payload["phase"] == "RF2"
    assert payload["checkpoint"] == "RF2.6"
    assert payload["status"] == "ready"
    assert payload["errors"] == []
    assert payload["runtime_changed_by_rf2_6"] is True
    assert payload["runtime_change_type"] == "downloadable_provenance_manifest_artifact_runtime_link"
    assert payload["dependency_versions_changed_by_rf2_6"] is False
    assert payload["dockerfiles_changed_by_rf2_6"] is False
    assert payload["api_endpoint_added_by_rf2_6"] is False
    assert payload["db_schema_migration_added_by_rf2_6"] is False
    assert payload["visual_qa_runtime_added_by_rf2_6"] is False
    assert payload["provenance_manifest_emitted_by_rf2_6"] is True


def test_rf2_6_generation_path_registers_downloadable_manifest_artifact() -> None:
    service, artifact_service = build_service()

    result = service.generate_deck_from_approved_plan_with_provenance(
        sample_plan(),
        session_id="ses_rf2_6",
        task_id="task_generate_rf2_6",
        presentation_id="pres_rf2_6",
        plan_snapshot_id="plansnap_generate_rf2_6",
        render_mode="adaptive",
        template_id="",
        artifact_filename="rf2-6-generated.pptx",
    )

    manifest = result.provenance_result.manifest
    manifest_artifact = result.provenance_result.manifest_artifact

    assert result.lifecycle_result.artifact in artifact_service.items
    assert manifest_artifact in artifact_service.items
    assert manifest_artifact.content_type == PROVENANCE_MANIFEST_CONTENT_TYPE
    assert manifest_artifact.filename == "rf2-6-generated.provenance.json"
    assert result.provenance_result.manifest_content.startswith(b"{")
    assert verify_manifest_digest(manifest)
    assert manifest["artifact"]["artifact_id"] == result.lifecycle_result.artifact.id
    assert manifest["plan_snapshot"]["plan_snapshot_id"] == "plansnap_generate_rf2_6"
    assert manifest["render_attempt"]["render_mode"] == "adaptive"
    assert manifest["render_attempt"]["template_source"] == "local_builtin_registry"
    assert len(manifest["event_refs"]) == 6
    assert result.safe_metadata["provenance_manifest_emitted_by_rf2_6"] is True
    assert result.safe_metadata["manifest_links_pptx_artifact"] is True
    assert result.safe_metadata["kimi_grade_supported"] is False


def test_rf2_6_retry_path_registers_manifest_with_parent_links_without_raw_instruction() -> None:
    service, artifact_service = build_service()
    generated = service.generate_deck_from_approved_plan_with_provenance(
        sample_plan(),
        session_id="ses_rf2_6",
        task_id="task_generate_rf2_6",
        presentation_id="pres_rf2_6",
        plan_snapshot_id="plansnap_generate_rf2_6",
        render_mode="adaptive",
        template_id="",
        artifact_filename="rf2-6-generated.pptx",
    )
    retry = service.retry_deck_from_saved_plan_with_provenance(
        saved_plan_snapshot_id="plansnap_generate_rf2_6",
        session_id="ses_rf2_6",
        retry_task_id="task_retry_rf2_6",
        parent_task_id="task_generate_rf2_6",
        presentation_id="pres_rf2_6",
        operator_instruction="Retry RF2.6 from the saved plan snapshot.",
        render_mode="template",
        template_id="business_clean",
        new_plan_snapshot_id="plansnap_retry_rf2_6",
        artifact_filename="rf2-6-retry.pptx",
    )

    manifest = retry.provenance_result.manifest
    manifest_artifact = retry.provenance_result.manifest_artifact

    assert generated.provenance_result.manifest_artifact in artifact_service.items
    assert manifest_artifact in artifact_service.items
    assert manifest_artifact.content_type == PROVENANCE_MANIFEST_CONTENT_TYPE
    assert manifest_artifact.filename == "rf2-6-retry.provenance.json"
    assert verify_manifest_digest(manifest)
    assert manifest["artifact"]["artifact_id"] == retry.retry_result.artifact.id
    assert manifest["retry_links"]["parent_task_id"] == "task_generate_rf2_6"
    assert manifest["retry_links"]["parent_plan_snapshot_id"] == "plansnap_generate_rf2_6"
    assert manifest["retry_links"]["new_plan_snapshot_id"] == "plansnap_retry_rf2_6"
    assert manifest["retry_links"]["retry_instruction_digest"].startswith("sha256:")
    assert "Retry RF2.6" not in json.dumps(manifest)
    assert len(manifest["event_refs"]) == 8
    assert retry.safe_metadata["raw_operator_instruction_stored"] is False
    assert retry.safe_metadata["provenance_manifest_emitted_by_rf2_6"] is True
    assert retry.safe_metadata["whole_project_kimi_level_supported"] is False


def test_rf2_6_build_manifest_helpers_are_valid_and_digest_detects_tampering() -> None:
    service, _artifact_service = build_service()
    generated = service.generate_deck_from_approved_plan_with_lifecycle(
        sample_plan(),
        session_id="ses_rf2_6",
        task_id="task_generate_rf2_6",
        presentation_id="pres_rf2_6",
        plan_snapshot_id="plansnap_generate_rf2_6",
        render_mode="adaptive",
        template_id="",
        artifact_filename="rf2-6-generated.pptx",
    )
    generation_manifest = build_generation_provenance_manifest(generated)
    assert verify_manifest_digest(generation_manifest)

    retry_result = service.retry_deck_from_saved_plan(
        saved_plan_snapshot_id="plansnap_generate_rf2_6",
        session_id="ses_rf2_6",
        retry_task_id="task_retry_rf2_6",
        parent_task_id="task_generate_rf2_6",
        presentation_id="pres_rf2_6",
        operator_instruction="Retry RF2.6 from saved plan.",
        render_mode="template",
        template_id="business_clean",
        new_plan_snapshot_id="plansnap_retry_rf2_6",
        artifact_filename="rf2-6-retry.pptx",
    )
    retry_manifest = build_retry_provenance_manifest(retry_result)
    assert verify_manifest_digest(retry_manifest)

    tampered = json.loads(json.dumps(retry_manifest))
    tampered["artifact"]["filename"] = "tampered.pptx"
    assert not verify_manifest_digest(tampered)


def test_rf2_6_production_readiness_gate_mentions_manifest_runtime() -> None:
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "Slides provenance manifest runtime" in gate
    assert "scripts/kw_slides_provenance_manifest_runtime_check.py" in gate
    assert "docs/codex/SLIDES_PROVENANCE_MANIFEST_RUNTIME.md" in gate
    assert "backend/tests/smoke/test_rf2_6_slides_provenance_manifest_runtime.py" in gate
