#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "docs/codex/SLIDES_APPROVED_PLAN_RUNTIME.md",
    "backend/app/services/slides_service/approved_plan.py",
    "scripts/kw_slides_approved_plan_runtime_check.py",
    "backend/tests/smoke/test_rf2_2_slides_approved_plan_runtime.py",
    "backend/app/services/slides_service/service.py",
    "backend/app/services/slides_service/__init__.py",
)

REQUIRED_MARKERS = {
    "approved_plan_module_request": ("backend/app/services/slides_service/approved_plan.py", "class ApprovedPlanRenderRequest"),
    "approved_plan_module_result": ("backend/app/services/slides_service/approved_plan.py", "class ApprovedPlanRenderResult"),
    "approved_plan_render_function": ("backend/app/services/slides_service/approved_plan.py", "def render_approved_plan_to_pptx("),
    "unapproved_rejection": ("backend/app/services/slides_service/approved_plan.py", "approval_status='approved'"),
    "checksum_metadata": ("backend/app/services/slides_service/approved_plan.py", "checksum_sha256"),
    "service_method": ("backend/app/services/slides_service/service.py", "def generate_deck_from_approved_plan("),
    "init_export": ("backend/app/services/slides_service/__init__.py", "ApprovedPlanRenderRequest"),
    "production_doc": ("docs/codex/SLIDES_APPROVED_PLAN_RUNTIME.md", "approved plan → deterministic PPTX bytes + safe metadata"),
}

CORE_PPTX_PARTS = (
    "[Content_Types].xml",
    "_rels/.rels",
    "docProps/core.xml",
    "docProps/app.xml",
    "ppt/presentation.xml",
)


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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def marker_present(repo_root: Path, rel: str, marker: str) -> bool:
    path = repo_root / rel
    return path.exists() and marker in read_text(path)


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing RF2.2 required file: {rel}")

    for name, (rel, marker) in REQUIRED_MARKERS.items():
        if not marker_present(repo_root, rel, marker):
            errors.append(f"missing RF2.2 marker: {name}")

    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch != "7_Runtime_Foundation":
            errors.append(f"expected branch 7_Runtime_Foundation, got {branch}")

    return errors


def build_sample_plan() -> Any:
    from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

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


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.slides_service import ApprovedPlanRenderRequest, SlidesService
    from backend.app.services.slides_service.approved_plan import render_approved_plan_to_pptx

    plan = build_sample_plan()
    request = ApprovedPlanRenderRequest(
        plan=plan,
        plan_snapshot_id="plansnap_rf2_2_approved",
        approval_status="approved",
        render_mode="adaptive",
        template_id="business_clean",
        session_id="ses_rf2_2",
        task_id="task_rf2_2",
        presentation_id="pres_rf2_2",
        artifact_filename="rf2-2-approved-plan.pptx",
    )

    direct = render_approved_plan_to_pptx(request)
    direct_again = render_approved_plan_to_pptx(request)
    via_service = SlidesService().generate_deck_from_approved_plan(
        plan,
        plan_snapshot_id="plansnap_rf2_2_approved",
        approval_status="approved",
        render_mode="adaptive",
        template_id="business_clean",
        session_id="ses_rf2_2",
        task_id="task_rf2_2",
        presentation_id="pres_rf2_2",
        artifact_filename="rf2-2-approved-plan.pptx",
    )

    errors: list[str] = []
    if direct.artifact_content != direct_again.artifact_content:
        errors.append("approved-plan render is not deterministic across repeated calls")
    if direct.checksum_sha256 != direct_again.checksum_sha256:
        errors.append("approved-plan checksum is not deterministic")
    if direct.checksum_sha256 != via_service.checksum_sha256:
        errors.append("service method checksum differs from direct approved-plan renderer")
    if not direct.artifact_content.startswith(b"PK"):
        errors.append("approved-plan PPTX payload does not start with ZIP magic PK")
    if direct.size_bytes != len(direct.artifact_content):
        errors.append("approved-plan size_bytes does not match payload length")
    if direct.slide_count != len(plan.slides):
        errors.append("approved-plan slide_count does not match plan")
    if direct.safe_metadata.get("kimi_grade_supported") is not False:
        errors.append("RF2.2 must not claim Kimi-grade support")
    if direct.safe_metadata.get("whole_project_kimi_level_supported") is not False:
        errors.append("RF2.2 must not claim whole-project Kimi-level support")

    names: set[str] = set()
    try:
        with zipfile.ZipFile(BytesIO(direct.artifact_content), "r") as pptx:
            names = set(pptx.namelist())
    except Exception as exc:
        errors.append(f"failed to inspect approved-plan PPTX zip: {exc}")

    for part in CORE_PPTX_PARTS:
        if part not in names:
            errors.append(f"approved-plan PPTX is missing core part: {part}")

    rejected_unapproved = False
    try:
        render_approved_plan_to_pptx(
            ApprovedPlanRenderRequest(
                plan=plan,
                plan_snapshot_id="plansnap_rf2_2_unapproved",
                approval_status="draft",
                render_mode="adaptive",
                template_id="business_clean",
            )
        )
    except ValueError:
        rejected_unapproved = True
    if not rejected_unapproved:
        errors.append("approved-plan renderer did not reject unapproved plan")

    rejected_missing_template = False
    try:
        render_approved_plan_to_pptx(
            ApprovedPlanRenderRequest(
                plan=plan,
                plan_snapshot_id="plansnap_rf2_2_template_missing",
                approval_status="approved",
                render_mode="template",
                template_id="",
            )
        )
    except ValueError:
        rejected_missing_template = True
    if not rejected_missing_template:
        errors.append("approved-plan renderer did not reject template mode without template_id")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "approved_plan_runtime_supported": not errors,
        "approved_plan_runtime_scope": "minimal_backend_runtime_bridge",
        "kimi_grade_supported": False,
        "product_grade_supported": False,
        "whole_project_kimi_level_supported": False,
        "render_mode": direct.render_mode,
        "template_id": direct.template_id,
        "content_type": direct.content_type,
        "artifact_filename": direct.artifact_filename,
        "payload_starts_with_pk": direct.artifact_content.startswith(b"PK"),
        "size_bytes": direct.size_bytes,
        "checksum_sha256": direct.checksum_sha256,
        "deterministic_bytes": direct.artifact_content == direct_again.artifact_content,
        "slide_count": direct.slide_count,
        "outline_count": len(direct.outline),
        "safe_event_types": list(direct.safe_event_types),
        "safe_metadata_keys": sorted(direct.safe_metadata.keys()),
        "core_parts_present": sorted(part for part in CORE_PPTX_PARTS if part in names),
        "rejected_unapproved_plan": rejected_unapproved,
        "rejected_template_mode_without_template_id": rejected_missing_template,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready=require_ready)
    smoke = run_runtime_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    errors = list(static_errors)
    errors.extend(smoke.get("errors", []))

    return {
        "mode": "slides-approved-plan-runtime",
        "phase": "RF2",
        "checkpoint": "RF2.2",
        "network_required": False,
        "runtime_changed_by_rf2_2": True,
        "runtime_change_type": "additive_backend_service_path",
        "dependency_versions_changed_by_rf2_2": False,
        "dockerfiles_changed_by_rf2_2": False,
        "frontend_runtime_changed_by_rf2_2": False,
        "llm_topology_changed_by_rf2_2": False,
        "browser_runtime_changed_by_rf2_2": False,
        "api_endpoint_added_by_rf2_2": False,
        "persistence_added_by_rf2_2": False,
        "provenance_manifest_emitted_by_rf2_2": False,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "runtime_smoke": smoke,
        "next_recommended_step": "RF2.3 — Plan snapshot persistence and task event stream runtime wiring",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RF2.2 approved-plan slides runtime check.")
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
