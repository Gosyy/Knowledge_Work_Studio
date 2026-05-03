#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "docs/codex/SLIDES_RENDER_MODE_RUNTIME_HARDENING.md",
    "backend/app/services/slides_service/render_mode_runtime.py",
    "backend/app/services/slides_service/approved_plan.py",
    "backend/app/services/slides_service/approved_plan_lifecycle.py",
    "backend/app/services/slides_service/saved_plan_retry.py",
    "backend/app/services/slides_service/service.py",
    "backend/app/services/slides_service/__init__.py",
    "scripts/kw_slides_render_mode_runtime_check.py",
    "backend/tests/smoke/test_rf2_5_slides_render_mode_runtime.py",
)

REQUIRED_MARKERS = {
    "runtime_request": ("backend/app/services/slides_service/render_mode_runtime.py", "class RenderModeRuntimeRequest"),
    "runtime_result": ("backend/app/services/slides_service/render_mode_runtime.py", "class RenderModeRuntimeResult"),
    "runtime_resolver": ("backend/app/services/slides_service/render_mode_runtime.py", "def resolve_render_mode_runtime("),
    "external_download_guard": ("backend/app/services/slides_service/render_mode_runtime.py", "EXTERNAL_TEMPLATE_DOWNLOAD_ALLOWED = False"),
    "approved_plan_runtime_usage": ("backend/app/services/slides_service/approved_plan.py", "resolve_render_mode_runtime"),
    "approved_plan_metadata": ("backend/app/services/slides_service/approved_plan.py", "render_mode_runtime.as_safe_metadata()"),
    "lifecycle_metadata": ("backend/app/services/slides_service/approved_plan_lifecycle.py", "render_mode_runtime_hardened"),
    "retry_metadata": ("backend/app/services/slides_service/saved_plan_retry.py", "render_mode_runtime_hardened"),
    "service_method": ("backend/app/services/slides_service/service.py", "def validate_render_mode_runtime("),
    "init_export": ("backend/app/services/slides_service/__init__.py", "RenderModeRuntimeRequest"),
    "doc_no_overclaim": ("docs/codex/SLIDES_RENDER_MODE_RUNTIME_HARDENING.md", "RF2.5 is required infrastructure for Kimi-level adaptive/template UX, but it does not reach Kimi-level."),
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
            errors.append(f"missing RF2.5 required file: {rel}")

    for name, (rel, marker) in REQUIRED_MARKERS.items():
        if not marker_present(repo_root, rel, marker):
            errors.append(f"missing RF2.5 marker: {name}")

    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch != "7_Runtime_Foundation":
            errors.append(f"expected branch 7_Runtime_Foundation, got {branch}")

    return errors


def build_sample_plan() -> Any:
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

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



def _metadata_string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_metadata_string_values(item))
        return values
    if isinstance(value, (list, tuple, set)):
        values = []
        for item in value:
            values.extend(_metadata_string_values(item))
        return values
    return []


def _raises_value_error(fn: Any) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.domain import Presentation
    from backend.app.services.slides_service import PresentationPlanSnapshotService, SlidesService
    from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderRequest, render_approved_plan_to_pptx
    from backend.app.services.slides_service.render_mode_runtime import (
        RenderModeRuntimeRequest,
        resolve_render_mode_runtime,
        slides_render_mode_runtime_capabilities,
    )

    plan = build_sample_plan()
    adaptive_policy = resolve_render_mode_runtime(
        RenderModeRuntimeRequest(
            render_mode="adaptive",
            template_id="",
            plan_snapshot_id="plansnap_rf2_5_policy",
            approved_plan=True,
        )
    )
    template_policy = resolve_render_mode_runtime(
        RenderModeRuntimeRequest(
            render_mode="template",
            template_id="business_clean",
            plan_snapshot_id="plansnap_rf2_5_policy",
            approved_plan=True,
        )
    )
    adaptive_render = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=plan,
            plan_snapshot_id="plansnap_rf2_5_adaptive",
            approval_status="approved",
            render_mode="adaptive",
            template_id="",
            artifact_filename="rf2-5-adaptive.pptx",
        )
    )
    template_render = render_approved_plan_to_pptx(
        ApprovedPlanRenderRequest(
            plan=plan,
            plan_snapshot_id="plansnap_rf2_5_template",
            approval_status="approved",
            render_mode="template",
            template_id="business_clean",
            artifact_filename="rf2-5-template.pptx",
        )
    )

    presentation = Presentation(
        id="pres_rf2_5",
        session_id="ses_rf2_5",
        current_file_id=None,
        presentation_type="slides",
        title="RF2.5 Render Modes",
    )
    snapshot_repo = _SnapshotRepo()
    artifact_service = _ArtifactService()
    plan_snapshot_service = PresentationPlanSnapshotService(
        snapshots=snapshot_repo,
        presentations=_PresentationRepo(presentation),
        presentation_versions=_PresentationVersionRepo(),
    )
    plan_snapshot_service.create_snapshot(
        presentation_id="pres_rf2_5",
        plan=plan,
        created_from_task_id="task_parent_rf2_5",
        change_summary="Saved parent plan for render mode retry.",
        snapshot_id="plansnap_parent_rf2_5",
    )
    service = SlidesService(
        plan_snapshot_service=plan_snapshot_service,
        artifact_service=artifact_service,
    )
    service_policy = service.validate_render_mode_runtime(
        render_mode="template",
        template_id="business_clean",
        plan_snapshot_id="plansnap_service_rf2_5",
        approved_plan=True,
    )
    retry_result = service.retry_deck_from_saved_plan(
        saved_plan_snapshot_id="plansnap_parent_rf2_5",
        session_id="ses_rf2_5",
        retry_task_id="task_retry_rf2_5",
        parent_task_id="task_parent_rf2_5",
        presentation_id="pres_rf2_5",
        operator_instruction="Retry RF2.5 using the saved approved plan.",
        render_mode="template",
        template_id="business_clean",
        new_plan_snapshot_id="plansnap_retry_rf2_5",
        artifact_filename="rf2-5-retry-template.pptx",
    )

    rejected_missing_template = _raises_value_error(
        lambda: render_approved_plan_to_pptx(
            ApprovedPlanRenderRequest(
                plan=plan,
                plan_snapshot_id="plansnap_missing_template_rf2_5",
                approval_status="approved",
                render_mode="template",
                template_id="",
            )
        )
    )
    rejected_external_template = _raises_value_error(
        lambda: render_approved_plan_to_pptx(
            ApprovedPlanRenderRequest(
                plan=plan,
                plan_snapshot_id="plansnap_external_template_rf2_5",
                approval_status="approved",
                render_mode="template",
                template_id="https://templates.example.com/business_clean.pptx",
            )
        )
    )
    rejected_path_template = _raises_value_error(
        lambda: render_approved_plan_to_pptx(
            ApprovedPlanRenderRequest(
                plan=plan,
                plan_snapshot_id="plansnap_path_template_rf2_5",
                approval_status="approved",
                render_mode="template",
                template_id="../business_clean",
            )
        )
    )
    rejected_unknown_template = _raises_value_error(
        lambda: render_approved_plan_to_pptx(
            ApprovedPlanRenderRequest(
                plan=plan,
                plan_snapshot_id="plansnap_unknown_template_rf2_5",
                approval_status="approved",
                render_mode="template",
                template_id="unknown_remote_catalog_template",
            )
        )
    )

    approved_metadata = adaptive_render.safe_metadata
    template_metadata = template_render.safe_metadata
    retry_metadata = retry_result.safe_metadata
    policy_keys = {
        "render_mode_runtime_hardened",
        "template_source",
        "layout_policy",
        "template_id_required",
        "template_locked",
        "adaptive_layout_selection_enabled",
        "external_template_download_allowed",
        "local_template_registry_enforced",
    }
    approved_has_policy = policy_keys <= set(approved_metadata)
    template_has_policy = policy_keys <= set(template_metadata)
    retry_has_policy = policy_keys <= set(retry_metadata)
    forbidden_value_fragments = ("https://", "http://", "Retry RF2.5")
    metadata_values_text = json.dumps(
        _metadata_string_values({"approved": approved_metadata, "template": template_metadata, "retry": retry_metadata}),
        sort_keys=True,
    )
    safe_metadata_only = not any(fragment in metadata_values_text for fragment in forbidden_value_fragments)

    errors: list[str] = []
    if adaptive_policy.resolved_template_id != "business_clean":
        errors.append("adaptive render mode did not resolve to local default business_clean")
    if template_policy.resolved_template_id != "business_clean" or not template_policy.template_locked:
        errors.append("template render mode did not lock explicit local template_id")
    if service_policy.resolved_template_id != "business_clean":
        errors.append("SlidesService render mode validation did not resolve local template")
    if adaptive_render.safe_metadata.get("external_template_download_allowed") is not False:
        errors.append("adaptive approved-plan metadata must forbid external template downloads")
    if template_render.safe_metadata.get("template_locked") is not True:
        errors.append("template approved-plan metadata must mark template_locked")
    if retry_metadata.get("template_locked") is not True:
        errors.append("retry metadata must preserve template mode lock")
    if not rejected_missing_template:
        errors.append("template mode without template_id was not rejected")
    if not rejected_external_template:
        errors.append("external template reference was not rejected")
    if not rejected_path_template:
        errors.append("path-like template reference was not rejected")
    if not rejected_unknown_template:
        errors.append("unknown local template_id was not rejected")
    if not approved_has_policy or not template_has_policy or not retry_has_policy:
        errors.append("render mode policy metadata is missing from approved/template/retry path")
    if not adaptive_render.artifact_content.startswith(b"PK") or not template_render.artifact_content.startswith(b"PK"):
        errors.append("approved render output is not PPTX/ZIP payload")
    if not retry_result.render_result.artifact_content.startswith(b"PK"):
        errors.append("retry render output is not PPTX/ZIP payload")
    if not safe_metadata_only:
        errors.append("safe metadata contains forbidden raw/external fragments")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "render_mode_runtime_hardened": not errors,
        "adaptive_mode_supported": adaptive_policy.render_mode == "adaptive",
        "template_mode_supported": template_policy.render_mode == "template",
        "adaptive_uses_local_default_template": adaptive_policy.resolved_template_id == "business_clean",
        "template_requires_explicit_template_id": rejected_missing_template,
        "template_mode_locks_template_id": template_policy.template_locked,
        "external_template_download_allowed": False,
        "unsupported_template_rejected": rejected_unknown_template,
        "external_template_reference_rejected": rejected_external_template,
        "template_path_traversal_rejected": rejected_path_template,
        "approved_plan_metadata_contains_render_mode_policy": approved_has_policy and template_has_policy,
        "retry_metadata_contains_render_mode_policy": retry_has_policy,
        "safe_metadata_only": safe_metadata_only,
        "payload_starts_with_pk": (
            adaptive_render.artifact_content.startswith(b"PK")
            and template_render.artifact_content.startswith(b"PK")
            and retry_result.render_result.artifact_content.startswith(b"PK")
        ),
        "capabilities": slides_render_mode_runtime_capabilities(),
        "adaptive_metadata": approved_metadata,
        "template_metadata": template_metadata,
        "retry_metadata_keys": sorted(retry_metadata.keys()),
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
        "mode": "slides-render-mode-runtime-hardening",
        "phase": "RF2",
        "checkpoint": "RF2.5",
        "network_required": False,
        "runtime_changed_by_rf2_5": True,
        "runtime_change_type": "adaptive_template_local_render_mode_runtime_hardening",
        "dependency_versions_changed_by_rf2_5": False,
        "dockerfiles_changed_by_rf2_5": False,
        "frontend_runtime_changed_by_rf2_5": False,
        "llm_topology_changed_by_rf2_5": False,
        "browser_runtime_changed_by_rf2_5": False,
        "api_endpoint_added_by_rf2_5": False,
        "db_schema_migration_added_by_rf2_5": False,
        "queue_or_event_store_migration_added_by_rf2_5": False,
        "provenance_manifest_emitted_by_rf2_5": False,
        "visual_qa_runtime_added_by_rf2_5": False,
        "runtime_smoke": smoke,
        "next_recommended_step": "RF2.6 — Slides provenance manifest emitted as downloadable artifact",
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RF2.5 slides render mode runtime hardening check.")
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
