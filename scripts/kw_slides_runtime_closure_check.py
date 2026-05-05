#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "docs/codex/SLIDES_RUNTIME_RF2_CLOSURE.md",
    "backend/app/services/slides_service/runtime_closure.py",
    "scripts/kw_slides_runtime_closure_check.py",
    "backend/tests/smoke/test_rf2_7_slides_runtime_closure.py",
    "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md",
    "docs/codex/RUNTIME_FOUNDATION_PHASE_PLAN.md",
    "scripts/kw_production_readiness_gate.py",
    "backend/app/services/slides_service/__init__.py",
    "backend/app/services/slides_service/service.py",
    "backend/app/services/slides_service/approved_plan.py",
    "backend/app/services/slides_service/approved_plan_lifecycle.py",
    "backend/app/services/slides_service/saved_plan_retry.py",
    "backend/app/services/slides_service/render_mode_runtime.py",
    "backend/app/services/slides_service/provenance_manifest_runtime.py",
    "scripts/kw_slides_approved_plan_runtime_check.py",
    "scripts/kw_slides_approved_plan_lifecycle_check.py",
    "scripts/kw_slides_saved_plan_retry_check.py",
    "scripts/kw_slides_render_mode_runtime_check.py",
    "scripts/kw_slides_provenance_manifest_runtime_check.py",
)

REQUIRED_MARKERS = {
    "closure_doc_route": ("docs/codex/SLIDES_RUNTIME_RF2_CLOSURE.md", "RF2_closure -> RF3 -> RF4 -> RF_closure -> K0"),
    "closure_module": ("backend/app/services/slides_service/runtime_closure.py", "def build_slides_runtime_closure_readiness("),
    "closure_validator": ("backend/app/services/slides_service/runtime_closure.py", "def validate_slides_runtime_closure_readiness("),
    "closure_export": ("backend/app/services/slides_service/__init__.py", "build_slides_runtime_closure_readiness"),
    "production_gate_step": ("scripts/kw_production_readiness_gate.py", "Slides RF2 runtime closure and readiness"),
    "production_gate_file": ("scripts/kw_production_readiness_gate.py", "scripts/kw_slides_runtime_closure_check.py"),
    "phase_plan_default_next": ("docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md", "RF2_closure -> RF3 -> RF4 -> RF_closure -> K0"),
    "runtime_foundation_default_next": ("docs/codex/RUNTIME_FOUNDATION_PHASE_PLAN.md", "RF2_closure -> RF3 -> RF4 -> RF_closure -> K0"),
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
            errors.append(f"missing RF2.7 required file: {rel}")

    for name, (rel, marker) in REQUIRED_MARKERS.items():
        if not marker_present(repo_root, rel, marker):
            errors.append(f"missing RF2.7 marker: {name}")

    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        allowed_branches = {"7_Runtime_Foundation", "8_K_Phase", "9_Product_Release_Hardening"}
        if branch not in allowed_branches:
            errors.append(f"expected branch 7_Runtime_Foundation, 8_K_Phase, or 9_Product_Release_Hardening, got {branch}")

    return errors


def build_sample_plan() -> Any:
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

    slides = (
        PlannedSlide(
            slide_id="rf2_7_001",
            slide_type=SlideType.TITLE,
            story_arc_stage=StoryArcStage.OPENING,
            title="RF2.7 Closure",
            bullets=("Slides runtime foundation", "Ready for RF2 closure"),
            layout_hint="title_slide",
        ),
        PlannedSlide(
            slide_id="rf2_7_002",
            slide_type=SlideType.CONTENT,
            story_arc_stage=StoryArcStage.ANALYSIS,
            title="Runtime path",
            bullets=("Approved plan", "Retry", "Render mode", "Provenance"),
            layout_hint="title_and_bullets",
        ),
        PlannedSlide(
            slide_id="rf2_7_003",
            slide_type=SlideType.CONCLUSION,
            story_arc_stage=StoryArcStage.CLOSE,
            title="Next route",
            bullets=("RF2_closure", "RF3", "RF4", "RF_closure", "K0"),
            layout_hint="conclusion",
        ),
    )
    return PresentationPlan(
        deck_title="RF2.7 Closure",
        deck_goal="Verify RF2 slides runtime foundation readiness.",
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
        return self.presentation if presentation_id == self.presentation.id else None

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
        self.contents: dict[str, bytes] = {}

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
            id=f"art_rf2_7_{len(self.items) + 1}",
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
        self.contents[artifact.id] = content
        return artifact


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.domain import Presentation
    from backend.app.services.slides_service import PresentationPlanSnapshotService, SlidesService
    from backend.app.services.slides_service.provenance_manifest_runtime import PROVENANCE_MANIFEST_CONTENT_TYPE
    from backend.app.services.slides_service.runtime_closure import (
        build_slides_runtime_closure_readiness,
        validate_slides_runtime_closure_readiness,
    )

    presentation = Presentation(
        id="pres_rf2_7",
        session_id="ses_rf2_7",
        current_file_id=None,
        presentation_type="slides",
        title="RF2.7 Closure",
    )
    artifact_service = _ArtifactService()
    snapshot_service = PresentationPlanSnapshotService(
        snapshots=_SnapshotRepo(),
        presentations=_PresentationRepo(presentation),
        presentation_versions=_PresentationVersionRepo(),
    )
    service = SlidesService(
        plan_snapshot_service=snapshot_service,
        artifact_service=artifact_service,
    )

    generation = service.generate_deck_from_approved_plan_with_provenance(
        build_sample_plan(),
        session_id="ses_rf2_7",
        task_id="task_rf2_7_generation",
        presentation_id="pres_rf2_7",
        render_mode="adaptive",
        template_id="business_clean",
        plan_snapshot_id="plansnap_rf2_7_generation",
        artifact_filename="rf2-7-generation.pptx",
    )

    retry = service.retry_deck_from_saved_plan_with_provenance(
        saved_plan_snapshot_id=generation.lifecycle_result.plan_snapshot.id,
        session_id="ses_rf2_7",
        retry_task_id="task_rf2_7_retry",
        parent_task_id="task_rf2_7_generation",
        presentation_id="pres_rf2_7",
        operator_instruction="Retry from the RF2.7 saved plan for closure readiness.",
        render_mode="template",
        template_id="business_clean",
        new_plan_snapshot_id="plansnap_rf2_7_retry",
        artifact_filename="rf2-7-retry.pptx",
    )

    readiness = build_slides_runtime_closure_readiness()
    readiness_errors = validate_slides_runtime_closure_readiness(readiness)

    errors: list[str] = list(readiness_errors)
    generation_manifest = generation.provenance_result.manifest
    retry_manifest = retry.provenance_result.manifest

    generation_manifest_ok = generation.provenance_result.manifest_artifact.content_type == PROVENANCE_MANIFEST_CONTENT_TYPE
    retry_manifest_ok = retry.provenance_result.manifest_artifact.content_type == PROVENANCE_MANIFEST_CONTENT_TYPE
    if not generation_manifest_ok:
        errors.append("generation provenance manifest artifact has wrong content type")
    if not retry_manifest_ok:
        errors.append("retry provenance manifest artifact has wrong content type")
    if generation_manifest.get("artifact", {}).get("artifact_id") != generation.lifecycle_result.artifact.id:
        errors.append("generation manifest does not link generated PPTX artifact")
    if retry_manifest.get("artifact", {}).get("artifact_id") != retry.retry_result.artifact.id:
        errors.append("retry manifest does not link retry PPTX artifact")
    if retry_manifest.get("retry_links", {}).get("parent_plan_snapshot_id") != generation.lifecycle_result.plan_snapshot.id:
        errors.append("retry manifest does not link parent plan snapshot")
    if generation.lifecycle_result.render_result.safe_metadata.get("render_mode_runtime_hardened") is not True:
        errors.append("generation render mode metadata is not hardened")
    if retry.retry_result.render_result.safe_metadata.get("render_mode_runtime_hardened") is not True:
        errors.append("retry render mode metadata is not hardened")
    if generation.provenance_result.safe_metadata.get("kimi_grade_supported") is not False:
        errors.append("RF2.7 must not claim generation Kimi-grade support")
    if retry.provenance_result.safe_metadata.get("whole_project_kimi_level_supported") is not False:
        errors.append("RF2.7 must not claim whole-project Kimi-level support")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "rf2_slides_path_ready_for_closure": readiness.rf2_slides_path_ready_for_closure and not errors,
        "closed_checkpoints": list(readiness.closed_checkpoints),
        "capabilities": list(readiness.capabilities),
        "next_route": list(readiness.next_route),
        "generation_provenance_supported": generation_manifest_ok,
        "retry_provenance_supported": retry_manifest_ok,
        "generation_manifest_links_pptx_artifact": generation_manifest.get("artifact", {}).get("artifact_id") == generation.lifecycle_result.artifact.id,
        "retry_manifest_links_pptx_artifact": retry_manifest.get("artifact", {}).get("artifact_id") == retry.retry_result.artifact.id,
        "retry_parent_links_present": retry_manifest.get("retry_links", {}).get("parent_plan_snapshot_id") == generation.lifecycle_result.plan_snapshot.id,
        "render_mode_runtime_hardened": (
            generation.lifecycle_result.render_result.safe_metadata.get("render_mode_runtime_hardened") is True
            and retry.retry_result.render_result.safe_metadata.get("render_mode_runtime_hardened") is True
        ),
        "k_phase_ready_to_start": readiness.k_phase_ready_to_start,
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
        "mode": "slides-runtime-rf2-closure-readiness",
        "phase": "RF2",
        "checkpoint": "RF2.7",
        "network_required": False,
        "runtime_changed_by_rf2_7": False,
        "runtime_change_type": "rf2_slides_runtime_closure_readiness_gate",
        "dependency_versions_changed_by_rf2_7": False,
        "dockerfiles_changed_by_rf2_7": False,
        "frontend_runtime_changed_by_rf2_7": False,
        "llm_topology_changed_by_rf2_7": False,
        "browser_runtime_changed_by_rf2_7": False,
        "api_endpoint_added_by_rf2_7": False,
        "db_schema_migration_added_by_rf2_7": False,
        "queue_or_event_store_migration_added_by_rf2_7": False,
        "provenance_manifest_runtime_already_present_from_rf2_6": True,
        "visual_qa_runtime_added_by_rf2_7": False,
        "k_phase_started_by_rf2_7": False,
        "rf2_slides_path_ready_for_closure": smoke.get("rf2_slides_path_ready_for_closure") is True,
        "runtime_smoke": smoke,
        "next_recommended_step": "RF2_closure — close RF2 slides runtime foundation before RF3",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RF2.7 slides runtime closure readiness check.")
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
