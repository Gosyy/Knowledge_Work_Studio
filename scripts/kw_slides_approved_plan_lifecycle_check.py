#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "docs/codex/SLIDES_APPROVED_PLAN_LIFECYCLE_RUNTIME.md",
    "backend/app/services/slides_service/approved_plan_lifecycle.py",
    "backend/app/services/slides_service/service.py",
    "backend/app/services/slides_service/__init__.py",
    "backend/app/composition.py",
    "scripts/kw_slides_approved_plan_lifecycle_check.py",
    "backend/tests/smoke/test_rf2_3_slides_approved_plan_lifecycle.py",
)

REQUIRED_MARKERS = {
    "lifecycle_request": ("backend/app/services/slides_service/approved_plan_lifecycle.py", "class ApprovedPlanLifecycleRequest"),
    "lifecycle_result": ("backend/app/services/slides_service/approved_plan_lifecycle.py", "class ApprovedPlanLifecycleResult"),
    "task_event": ("backend/app/services/slides_service/approved_plan_lifecycle.py", "class SlidesTaskEvent"),
    "lifecycle_function": ("backend/app/services/slides_service/approved_plan_lifecycle.py", "def render_approved_plan_with_lifecycle("),
    "rf2_3_sequence": ("backend/app/services/slides_service/approved_plan_lifecycle.py", "RF2_3_EVENT_SEQUENCE"),
    "safe_payload_filter": ("backend/app/services/slides_service/approved_plan_lifecycle.py", "def _safe_payload("),
    "service_method": ("backend/app/services/slides_service/service.py", "def generate_deck_from_approved_plan_with_lifecycle("),
    "service_snapshot_field": ("backend/app/services/slides_service/service.py", "plan_snapshot_service: object | None = None"),
    "service_artifact_field": ("backend/app/services/slides_service/service.py", "artifact_service: object | None = None"),
    "composition_snapshot_wire": ("backend/app/composition.py", "plan_snapshot_service=container.presentation_plan_snapshot_service"),
    "composition_artifact_wire": ("backend/app/composition.py", "artifact_service=container.artifact_service"),
    "init_export": ("backend/app/services/slides_service/__init__.py", "ApprovedPlanLifecycleRequest"),
    "doc_no_overclaim": ("docs/codex/SLIDES_APPROVED_PLAN_LIFECYCLE_RUNTIME.md", "RF2.3 is required infrastructure for Kimi-level, but it does not reach Kimi-level."),
}


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def marker_present(repo_root: Path, rel: str, marker: str) -> bool:
    path = repo_root / rel
    return path.exists() and marker in path.read_text(encoding="utf-8")


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing RF2.3 required file: {rel}")

    for name, (rel, marker) in REQUIRED_MARKERS.items():
        if not marker_present(repo_root, rel, marker):
            errors.append(f"missing RF2.3 marker: {name}")

    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch != "7_Runtime_Foundation":
            errors.append(f"expected branch 7_Runtime_Foundation, got {branch}")

    return errors


def build_sample_plan() -> Any:
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

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


class _PresentationRepo:
    def __init__(self, presentation: Any) -> None:
        self.presentation = presentation

    def get(self, presentation_id: str) -> Any | None:
        if presentation_id == self.presentation.id:
            return self.presentation
        return None

    def create(self, presentation: Any) -> Any:
        self.presentation = presentation
        return presentation

    def list_by_session(self, session_id: str) -> list[Any]:
        return [self.presentation] if self.presentation.session_id == session_id else []


class _PresentationVersionRepo:
    def list_by_presentation(self, presentation_id: str) -> list[Any]:
        return []

    def create(self, presentation_version: Any) -> Any:
        return presentation_version


class _SnapshotRepo:
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


class _ArtifactService:
    def __init__(self) -> None:
        self.items: list[Any] = []

    def create_artifact_from_bytes(
        self,
        *,
        session_id: str,
        task_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Any:
        from backend.app.domain import Artifact

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
        return artifact


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.domain import Presentation
    from backend.app.services.slides_service import PresentationPlanSnapshotService, SlidesService

    presentation = Presentation(
        id="pres_rf2_3",
        session_id="ses_rf2_3",
        current_file_id=None,
        presentation_type="slides",
        title="RF2.3 Lifecycle",
    )
    snapshot_repo = _SnapshotRepo()
    artifact_service = _ArtifactService()
    plan_snapshot_service = PresentationPlanSnapshotService(
        snapshots=snapshot_repo,
        presentations=_PresentationRepo(presentation),
        presentation_versions=_PresentationVersionRepo(),
    )
    service = SlidesService(
        plan_snapshot_service=plan_snapshot_service,
        artifact_service=artifact_service,
    )
    result = service.generate_deck_from_approved_plan_with_lifecycle(
        build_sample_plan(),
        session_id="ses_rf2_3",
        task_id="task_rf2_3",
        presentation_id="pres_rf2_3",
        plan_snapshot_id="plansnap_rf2_3",
        render_mode="adaptive",
        template_id="business_clean",
        artifact_filename="rf2-3-approved-plan.pptx",
    )

    errors: list[str] = []
    expected_events = (
        "slides.plan.approved",
        "slides.render_mode.selected",
        "slides.generation.started",
        "artifact.registered",
        "plan.snapshot.registered",
        "slides.generation.completed",
    )
    event_types = tuple(event.event_type for event in result.events)
    if event_types != expected_events:
        errors.append(f"unexpected RF2.3 event order: {event_types!r}")

    allowed_payload_keys = {
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
    forbidden_payload_keys = {"password", "secret", "token", "api_key", "client_secret", "database_url", "authorization"}
    for event in result.events:
        extra = set(event.safe_payload) - allowed_payload_keys
        forbidden = {key for key in event.safe_payload if key.lower() in forbidden_payload_keys}
        if extra:
            errors.append(f"event {event.event_type} has non-safe payload keys: {sorted(extra)}")
        if forbidden:
            errors.append(f"event {event.event_type} has forbidden payload keys: {sorted(forbidden)}")

    if result.plan_snapshot.id != "plansnap_rf2_3":
        errors.append("plan snapshot id was not persisted as requested")
    if not snapshot_repo.items:
        errors.append("plan snapshot was not persisted")
    if not artifact_service.items:
        errors.append("artifact was not registered")
    if not result.render_result.artifact_content.startswith(b"PK"):
        errors.append("rendered artifact is not a PPTX/ZIP payload")
    if result.safe_metadata.get("kimi_grade_supported") is not False:
        errors.append("RF2.3 must not claim Kimi-grade support")
    if result.safe_metadata.get("whole_project_kimi_level_supported") is not False:
        errors.append("RF2.3 must not claim whole-project Kimi-level support")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "approved_plan_lifecycle_supported": not errors,
        "plan_snapshot_persisted": bool(snapshot_repo.items),
        "artifact_registered": bool(artifact_service.items),
        "event_order_valid": event_types == expected_events,
        "safe_payload_only": not any(set(event.safe_payload) - allowed_payload_keys for event in result.events),
        "event_types": list(event_types),
        "event_count": len(result.events),
        "plan_snapshot_id": result.plan_snapshot.id,
        "artifact_id": result.artifact.id,
        "artifact_filename": result.artifact.filename,
        "payload_starts_with_pk": result.render_result.artifact_content.startswith(b"PK"),
        "kimi_grade_supported": False,
        "product_grade_supported": False,
        "whole_project_kimi_level_supported": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready=require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = list(static_errors)
    errors.extend(smoke.get("errors", []))

    return {
        "mode": "slides-approved-plan-lifecycle-runtime",
        "phase": "RF2",
        "checkpoint": "RF2.3",
        "network_required": False,
        "runtime_changed_by_rf2_3": True,
        "runtime_change_type": "approved_plan_snapshot_artifact_event_lifecycle_wiring",
        "dependency_versions_changed_by_rf2_3": False,
        "dockerfiles_changed_by_rf2_3": False,
        "frontend_runtime_changed_by_rf2_3": False,
        "llm_topology_changed_by_rf2_3": False,
        "browser_runtime_changed_by_rf2_3": False,
        "api_endpoint_added_by_rf2_3": False,
        "db_schema_migration_added_by_rf2_3": False,
        "saved_plan_retry_implemented_by_rf2_3": False,
        "provenance_manifest_emitted_by_rf2_3": False,
        "visual_qa_runtime_added_by_rf2_3": False,
        "runtime_smoke": smoke,
        "next_recommended_step": "RF2.4 — Saved-plan retry runtime path",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RF2.3 approved-plan lifecycle runtime check.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    report = build_report(repo_root, require_ready=args.require_ready)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
