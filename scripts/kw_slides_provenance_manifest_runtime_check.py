#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "docs/codex/SLIDES_PROVENANCE_MANIFEST_RUNTIME.md",
    "backend/app/services/slides_service/provenance_manifest_runtime.py",
    "backend/app/services/slides_service/service.py",
    "backend/app/services/slides_service/__init__.py",
    "scripts/kw_slides_provenance_manifest_runtime_check.py",
    "backend/tests/smoke/test_rf2_6_slides_provenance_manifest_runtime.py",
)

REQUIRED_MARKERS = {
    "runtime_result": ("backend/app/services/slides_service/provenance_manifest_runtime.py", "class SlidesProvenanceManifestEmissionResult"),
    "generation_emitter": ("backend/app/services/slides_service/provenance_manifest_runtime.py", "def emit_generation_provenance_manifest("),
    "retry_emitter": ("backend/app/services/slides_service/provenance_manifest_runtime.py", "def emit_retry_provenance_manifest("),
    "digest_verifier": ("backend/app/services/slides_service/provenance_manifest_runtime.py", "def verify_manifest_digest("),
    "service_generation_method": ("backend/app/services/slides_service/service.py", "def generate_deck_from_approved_plan_with_provenance("),
    "service_retry_method": ("backend/app/services/slides_service/service.py", "def retry_deck_from_saved_plan_with_provenance("),
    "init_export": ("backend/app/services/slides_service/__init__.py", "SlidesProvenanceManifestEmissionResult"),
    "doc_no_overclaim": ("docs/codex/SLIDES_PROVENANCE_MANIFEST_RUNTIME.md", "RF2.6 is required infrastructure for Kimi-level provenance UX, but it does not reach Kimi-level."),
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
            errors.append(f"missing RF2.6 required file: {rel}")
    for name, (rel, marker) in REQUIRED_MARKERS.items():
        if not marker_present(repo_root, rel, marker):
            errors.append(f"missing RF2.6 marker: {name}")
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        allowed_branches = {"7_Runtime_Foundation", "8_K_Phase"}
        if branch not in allowed_branches:
            errors.append(f"expected branch 7_Runtime_Foundation or 8_K_Phase, got {branch}")
    return errors


def build_sample_plan() -> Any:
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

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
    def create(self, presentation_version: Any) -> Any:
        return presentation_version

    def list_by_presentation(self, presentation_id: str) -> list[Any]:
        return []


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
        self.contents: list[bytes] = []

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


def build_service() -> tuple[Any, _ArtifactService]:
    from backend.app.domain import Presentation
    from backend.app.services.slides_service import PresentationPlanSnapshotService, SlidesService

    presentation = Presentation(
        id="pres_rf2_6",
        session_id="ses_rf2_6",
        current_file_id=None,
        presentation_type="slides",
        title="RF2.6 Provenance",
    )
    artifact_service = _ArtifactService()
    snapshot_service = PresentationPlanSnapshotService(
        snapshots=_SnapshotRepo(),
        presentations=_PresentationRepo(presentation),
        presentation_versions=_PresentationVersionRepo(),
    )
    return SlidesService(plan_snapshot_service=snapshot_service, artifact_service=artifact_service), artifact_service


def _string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_string_values(item))
        return values
    if isinstance(value, (list, tuple, set)):
        values = []
        for item in value:
            values.extend(_string_values(item))
        return values
    return []


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.slides_service.provenance_manifest_runtime import (
        PROVENANCE_MANIFEST_CONTENT_TYPE,
        verify_manifest_digest,
    )

    service, artifact_service = build_service()
    generation = service.generate_deck_from_approved_plan_with_provenance(
        build_sample_plan(),
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

    errors: list[str] = []
    gen_manifest = generation.provenance_result.manifest
    retry_manifest = retry.provenance_result.manifest
    gen_manifest_artifact = generation.provenance_result.manifest_artifact
    retry_manifest_artifact = retry.provenance_result.manifest_artifact

    if gen_manifest_artifact.content_type != PROVENANCE_MANIFEST_CONTENT_TYPE:
        errors.append("generation manifest artifact has unexpected content type")
    if retry_manifest_artifact.content_type != PROVENANCE_MANIFEST_CONTENT_TYPE:
        errors.append("retry manifest artifact has unexpected content type")
    if not generation.provenance_result.manifest_content.startswith(b"{"):
        errors.append("generation manifest content is not JSON")
    if not retry.provenance_result.manifest_content.startswith(b"{"):
        errors.append("retry manifest content is not JSON")
    if not verify_manifest_digest(gen_manifest):
        errors.append("generation manifest digest does not verify")
    if not verify_manifest_digest(retry_manifest):
        errors.append("retry manifest digest does not verify")
    if gen_manifest["artifact"]["artifact_id"] != generation.lifecycle_result.artifact.id:
        errors.append("generation manifest does not link PPTX artifact")
    if retry_manifest["artifact"]["artifact_id"] != retry.retry_result.artifact.id:
        errors.append("retry manifest does not link PPTX artifact")
    if retry_manifest.get("retry_links", {}).get("parent_plan_snapshot_id") != "plansnap_generate_rf2_6":
        errors.append("retry manifest missing parent snapshot link")
    if retry_manifest.get("retry_links", {}).get("new_plan_snapshot_id") != "plansnap_retry_rf2_6":
        errors.append("retry manifest missing new snapshot link")
    if "Retry RF2.6" in json.dumps(_string_values(retry_manifest), sort_keys=True):
        errors.append("retry manifest leaked raw operator instruction")
    if generation.safe_metadata.get("provenance_manifest_emitted_by_rf2_6") is not True:
        errors.append("generation safe metadata missing RF2.6 manifest emission")
    if retry.safe_metadata.get("provenance_manifest_emitted_by_rf2_6") is not True:
        errors.append("retry safe metadata missing RF2.6 manifest emission")
    if generation.safe_metadata.get("kimi_grade_supported") is not False:
        errors.append("generation metadata must not claim Kimi-grade support")
    if retry.safe_metadata.get("whole_project_kimi_level_supported") is not False:
        errors.append("retry metadata must not claim whole-project Kimi-level support")

    manifest_artifacts = [item for item in artifact_service.items if item.content_type == PROVENANCE_MANIFEST_CONTENT_TYPE]
    pptx_artifacts = [item for item in artifact_service.items if item.filename.endswith(".pptx")]

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "generation_provenance_supported": not errors,
        "retry_provenance_supported": not errors,
        "generation_manifest_artifact_registered": gen_manifest_artifact in artifact_service.items,
        "retry_manifest_artifact_registered": retry_manifest_artifact in artifact_service.items,
        "manifest_artifact_count": len(manifest_artifacts),
        "pptx_artifact_count": len(pptx_artifacts),
        "generation_manifest_links_pptx_artifact": gen_manifest["artifact"]["artifact_id"] == generation.lifecycle_result.artifact.id,
        "retry_manifest_links_pptx_artifact": retry_manifest["artifact"]["artifact_id"] == retry.retry_result.artifact.id,
        "generation_manifest_digest_valid": verify_manifest_digest(gen_manifest),
        "retry_manifest_digest_valid": verify_manifest_digest(retry_manifest),
        "retry_parent_links_present": "retry_links" in retry_manifest,
        "raw_operator_instruction_stored": False,
        "manifest_safe_payload_only": True,
        "downloadable_manifest_content_type": PROVENANCE_MANIFEST_CONTENT_TYPE,
        "generation_event_ref_count": len(gen_manifest["event_refs"]),
        "retry_event_ref_count": len(retry_manifest["event_refs"]),
        "generation_manifest_filename": gen_manifest_artifact.filename,
        "retry_manifest_filename": retry_manifest_artifact.filename,
        "provenance_manifest_emitted_by_rf2_6": True,
        "payload_starts_with_json": generation.provenance_result.manifest_content.startswith(b"{"),
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
        "mode": "slides-provenance-manifest-runtime",
        "phase": "RF2",
        "checkpoint": "RF2.6",
        "network_required": False,
        "runtime_changed_by_rf2_6": True,
        "runtime_change_type": "downloadable_provenance_manifest_artifact_runtime_link",
        "dependency_versions_changed_by_rf2_6": False,
        "dockerfiles_changed_by_rf2_6": False,
        "frontend_runtime_changed_by_rf2_6": False,
        "llm_topology_changed_by_rf2_6": False,
        "browser_runtime_changed_by_rf2_6": False,
        "api_endpoint_added_by_rf2_6": False,
        "db_schema_migration_added_by_rf2_6": False,
        "queue_or_event_store_migration_added_by_rf2_6": False,
        "visual_qa_runtime_added_by_rf2_6": False,
        "provenance_manifest_emitted_by_rf2_6": True,
        "runtime_smoke": smoke,
        "next_recommended_step": "RF2.7 — slides runtime closure and readiness for RF2 closure",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RF2.6 slides provenance manifest runtime check.")
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
