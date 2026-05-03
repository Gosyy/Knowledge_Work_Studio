#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "docs/codex/SLIDES_SAVED_PLAN_RETRY_RUNTIME.md",
    "backend/app/services/slides_service/saved_plan_retry.py",
    "backend/app/services/slides_service/service.py",
    "backend/app/services/slides_service/__init__.py",
    "scripts/kw_slides_saved_plan_retry_check.py",
    "backend/tests/smoke/test_rf2_4_slides_saved_plan_retry.py",
)

REQUIRED_MARKERS = {
    "retry_request": ("backend/app/services/slides_service/saved_plan_retry.py", "class SavedPlanRetryRequest"),
    "retry_result": ("backend/app/services/slides_service/saved_plan_retry.py", "class SavedPlanRetryResult"),
    "retry_function": ("backend/app/services/slides_service/saved_plan_retry.py", "def retry_saved_plan_with_lifecycle("),
    "retry_event_sequence": ("backend/app/services/slides_service/saved_plan_retry.py", "SLIDES_RETRY_EVENT_SEQUENCE"),
    "instruction_digest": ("backend/app/services/slides_service/saved_plan_retry.py", "retry_instruction_digest"),
    "raw_instruction_guard": ("backend/app/services/slides_service/saved_plan_retry.py", "\"raw_operator_instruction_stored\": False"),
    "service_method": ("backend/app/services/slides_service/service.py", "def retry_deck_from_saved_plan("),
    "init_export": ("backend/app/services/slides_service/__init__.py", "SavedPlanRetryRequest"),
    "doc_no_overclaim": ("docs/codex/SLIDES_SAVED_PLAN_RETRY_RUNTIME.md", "RF2.4 is required infrastructure for Kimi-level retry UX, but it does not reach Kimi-level."),
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
            errors.append(f"missing RF2.4 required file: {rel}")

    for name, (rel, marker) in REQUIRED_MARKERS.items():
        if not marker_present(repo_root, rel, marker):
            errors.append(f"missing RF2.4 marker: {name}")

    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch != "7_Runtime_Foundation":
            errors.append(f"expected branch 7_Runtime_Foundation, got {branch}")

    return errors


def build_sample_plan() -> Any:
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

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
        return artifact


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.domain import Presentation
    from backend.app.services.slides_service import PresentationPlanSnapshotService, SlidesService
    from backend.app.services.slides_service.plan_snapshot import serialize_presentation_plan

    presentation = Presentation(
        id="pres_rf2_4",
        session_id="ses_rf2_4",
        current_file_id=None,
        presentation_type="slides",
        title="RF2.4 Retry",
    )
    snapshot_repo = _SnapshotRepo()
    artifact_service = _ArtifactService()
    plan_snapshot_service = PresentationPlanSnapshotService(
        snapshots=snapshot_repo,
        presentations=_PresentationRepo(presentation),
        presentation_versions=_PresentationVersionRepo(),
    )
    saved_snapshot = plan_snapshot_service.create_snapshot(
        presentation_id="pres_rf2_4",
        plan=build_sample_plan(),
        created_from_task_id="task_parent_rf2_4",
        change_summary="Saved parent plan.",
        snapshot_id="plansnap_parent_rf2_4",
    )
    assert saved_snapshot.snapshot_json == serialize_presentation_plan(build_sample_plan())

    service = SlidesService(
        plan_snapshot_service=plan_snapshot_service,
        artifact_service=artifact_service,
    )
    result = service.retry_deck_from_saved_plan(
        saved_plan_snapshot_id="plansnap_parent_rf2_4",
        session_id="ses_rf2_4",
        retry_task_id="task_retry_rf2_4",
        parent_task_id="task_parent_rf2_4",
        presentation_id="pres_rf2_4",
        operator_instruction="Regenerate using the saved approved plan for RF2.4.",
        render_mode="adaptive",
        template_id="business_clean",
        new_plan_snapshot_id="plansnap_retry_rf2_4",
        artifact_filename="rf2-4-retry.pptx",
    )

    errors: list[str] = []
    expected_events = (
        "slides.retry.from_saved_plan.requested",
        "slides.retry.saved_plan_snapshot.loaded",
        "slides.retry.plan.validated",
        "slides.retry.render_mode.confirmed",
        "slides.retry.generation.started",
        "artifact.registered",
        "plan.snapshot.registered",
        "slides.retry.generation.completed",
    )
    event_types = tuple(event.event_type for event in result.events)
    if event_types != expected_events:
        errors.append(f"unexpected RF2.4 retry event order: {event_types!r}")

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
    forbidden_payload_keys = {"password", "secret", "token", "api_key", "client_secret", "database_url", "authorization", "operator_instruction"}
    for event in result.events:
        extra = set(event.safe_payload) - allowed_payload_keys
        forbidden = {key for key in event.safe_payload if key.lower() in forbidden_payload_keys}
        if extra:
            errors.append(f"event {event.event_type} has non-safe payload keys: {sorted(extra)}")
        if forbidden:
            errors.append(f"event {event.event_type} has forbidden payload keys: {sorted(forbidden)}")
        if "Regenerate using" in json.dumps(event.safe_payload):
            errors.append(f"event {event.event_type} leaked raw operator instruction")

    if result.saved_plan_snapshot.id != "plansnap_parent_rf2_4":
        errors.append("saved plan snapshot was not loaded")
    if result.new_plan_snapshot.id != "plansnap_retry_rf2_4":
        errors.append("new retry plan snapshot was not persisted")
    if not artifact_service.items:
        errors.append("retry artifact was not registered")
    if not result.render_result.artifact_content.startswith(b"PK"):
        errors.append("retry artifact is not a PPTX/ZIP payload")
    if result.safe_metadata.get("parent_plan_snapshot_id") != "plansnap_parent_rf2_4":
        errors.append("retry parent plan snapshot link missing")
    if result.safe_metadata.get("parent_task_id") != "task_parent_rf2_4":
        errors.append("retry parent task link missing")
    if result.safe_metadata.get("raw_operator_instruction_stored") is not False:
        errors.append("raw operator instruction must not be stored")
    if "Regenerate using" in json.dumps(result.safe_metadata):
        errors.append("safe metadata leaked raw operator instruction")
    if result.safe_metadata.get("kimi_grade_supported") is not False:
        errors.append("RF2.4 must not claim Kimi-grade support")
    if result.safe_metadata.get("whole_project_kimi_level_supported") is not False:
        errors.append("RF2.4 must not claim whole-project Kimi-level support")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "saved_plan_retry_supported": not errors,
        "saved_plan_snapshot_loaded": result.saved_plan_snapshot.id == "plansnap_parent_rf2_4",
        "new_plan_snapshot_persisted": result.new_plan_snapshot.id == "plansnap_retry_rf2_4",
        "new_artifact_registered": bool(artifact_service.items),
        "retry_event_order_valid": event_types == expected_events,
        "retry_parent_links_present": result.safe_metadata.get("parent_plan_snapshot_id") == "plansnap_parent_rf2_4",
        "safe_payload_only": not any(set(event.safe_payload) - allowed_payload_keys for event in result.events),
        "raw_operator_instruction_stored": result.safe_metadata.get("raw_operator_instruction_stored"),
        "retry_instruction_digest_present": "retry_instruction_digest" in result.safe_metadata,
        "event_types": list(event_types),
        "event_count": len(result.events),
        "parent_plan_snapshot_id": result.saved_plan_snapshot.id,
        "new_plan_snapshot_id": result.new_plan_snapshot.id,
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
        "mode": "slides-saved-plan-retry-runtime",
        "phase": "RF2",
        "checkpoint": "RF2.4",
        "network_required": False,
        "runtime_changed_by_rf2_4": True,
        "runtime_change_type": "saved_plan_snapshot_retry_runtime_path",
        "dependency_versions_changed_by_rf2_4": False,
        "dockerfiles_changed_by_rf2_4": False,
        "frontend_runtime_changed_by_rf2_4": False,
        "llm_topology_changed_by_rf2_4": False,
        "browser_runtime_changed_by_rf2_4": False,
        "api_endpoint_added_by_rf2_4": False,
        "db_schema_migration_added_by_rf2_4": False,
        "queue_or_event_store_migration_added_by_rf2_4": False,
        "provenance_manifest_emitted_by_rf2_4": False,
        "visual_qa_runtime_added_by_rf2_4": False,
        "runtime_smoke": smoke,
        "next_recommended_step": "RF2.5 — Adaptive/template local render mode runtime hardening",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RF2.4 saved-plan retry runtime check.")
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
