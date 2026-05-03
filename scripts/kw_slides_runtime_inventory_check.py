#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "docs/codex/SLIDES_RUNTIME_CAPABILITY_INVENTORY.md",
    "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md",
    "scripts/kw_slides_runtime_inventory_check.py",
    "scripts/kw_slides_runtime_phase_check.py",
    "backend/tests/smoke/test_rf2_1_slides_runtime_inventory.py",
    "backend/app/services/slides_service/outline.py",
    "backend/app/services/slides_service/service.py",
    "backend/app/services/slides_service/entrypoint.py",
    "backend/app/services/slides_service/generator.py",
    "backend/app/services/slides_service/plan_snapshot.py",
    "backend/app/services/slides_service/revision.py",
    "backend/app/api/routes/presentations.py",
    "backend/app/services/presentation_catalog_service.py",
    "frontend/src/lib/api/presentations.ts",
    "frontend/src/components/presentations/slides-plan-editor-panel.tsx",
    "frontend/tests/e2e/slides-plan-editor-smoke.spec.ts",
    "backend/tests/services/test_slides_service.py",
)

REQUIRED_DOC_PHRASES = (
    "RF2.1 checkpoint",
    "Critical interpretation rule",
    "Whole-project Kimi-level rule",
    "Kimi-level target applies to the whole slides product loop",
    "not enough to claim that KW Studio works at the level of Kimi slides",
    "Baseline runtime that is currently present",
    "Partial runtime baseline",
    "Product-quality gaps",
    "Contract-only or not-yet-runtime RF2 work",
    "Baseline smoke",
    "Kimi-grade support remains explicitly false",
    "RF2.2 — Minimal deterministic PPTX generation from approved plan",
    "do not overclaim Kimi-level output until real product-quality gates exist",
    "do not run `npm audit fix --force`",
)

RUNTIME_MARKERS = {
    "outline_deterministic_segment_split": ("backend/app/services/slides_service/outline.py", "normalized.split(\".\")"),
    "outline_bounded_bullets": ("backend/app/services/slides_service/outline.py", "_MAX_BULLETS_PER_SLIDE"),
    "slides_service_generate_deck": ("backend/app/services/slides_service/service.py", "def generate_deck("),
    "slides_service_returns_transform_output": ("backend/app/services/slides_service/service.py", "SlidesTransformOutput("),
    "slides_service_source_grounding": ("backend/app/services/slides_service/service.py", "build_source_grounded_plan("),
    "slides_service_generated_visuals": ("backend/app/services/slides_service/service.py", "_attach_generated_visuals("),
    "entrypoint_generate": ("backend/app/services/slides_service/entrypoint.py", "def generate("),
    "pptx_from_plan": ("backend/app/services/slides_service/generator.py", "def generate_pptx_from_plan("),
    "deterministic_zip_timestamp": ("backend/app/services/slides_service/generator.py", "DETERMINISTIC_ZIP_TIMESTAMP"),
    "presentation_list_route": ("backend/app/api/routes/presentations.py", '"/sessions/{session_id}/presentations"'),
    "presentation_versions_route": ("backend/app/api/routes/presentations.py", '"/presentations/{presentation_id}/versions"'),
    "presentation_current_plan_route": ("backend/app/api/routes/presentations.py", '"/presentations/{presentation_id}/plan"'),
    "presentation_version_plan_route": ("backend/app/api/routes/presentations.py", '"/presentations/{presentation_id}/versions/{version_id}/plan"'),
    "presentation_plan_diff_route": ("backend/app/api/routes/presentations.py", '"/presentations/{presentation_id}/revisions/{version_id}/diff"'),
    "presentation_catalog_service": ("backend/app/services/presentation_catalog_service.py", "class PresentationCatalogService"),
    "plan_snapshot_service": ("backend/app/services/slides_service/plan_snapshot.py", "class PresentationPlanSnapshotService"),
    "deck_revision_service": ("backend/app/services/slides_service/revision.py", "class DeckRevisionService"),
    "frontend_presentations_api": ("frontend/src/lib/api/presentations.ts", "getPresentation("),
    "frontend_plan_editor": ("frontend/src/components/presentations/slides-plan-editor-panel.tsx", "SlidesPlanEditorPanel"),
    "frontend_plan_editor_e2e": ("frontend/tests/e2e/slides-plan-editor-smoke.spec.ts", "slides plan editor"),
    "service_test_openxml": ("backend/tests/services/test_slides_service.py", "test_slides_service_generates_valid_openxml_pptx_payload"),
    "service_test_media_registry": ("backend/tests/services/test_slides_service.py", "test_slides_service_registers_generated_visuals_to_storage_when_context_available"),
}

CORE_PPTX_PARTS = (
    "[Content_Types].xml",
    "_rels/.rels",
    "docProps/core.xml",
    "docProps/app.xml",
    "ppt/presentation.xml",
    "ppt/_rels/presentation.xml.rels",
    "ppt/theme/theme1.xml",
    "ppt/slideMasters/slideMaster1.xml",
    "ppt/slideLayouts/slideLayout1.xml",
)


@dataclass(frozen=True)
class Capability:
    capability_id: str
    status: str
    evidence: list[str]
    next_step: str | None = None


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


def collect_marker_report(repo_root: Path) -> dict[str, bool]:
    return {name: marker_present(repo_root, rel, marker) for name, (rel, marker) in RUNTIME_MARKERS.items()}


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing RF2.1 required file: {rel}")

    doc = repo_root / "docs/codex/SLIDES_RUNTIME_CAPABILITY_INVENTORY.md"
    if doc.exists():
        content = read_text(doc)
        for phrase in REQUIRED_DOC_PHRASES:
            if phrase not in content:
                errors.append(f"RF2.1 inventory doc is missing phrase: {phrase}")

    marker_report = collect_marker_report(repo_root)
    for name, ok in marker_report.items():
        if not ok:
            errors.append(f"missing runtime marker: {name}")

    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch != "7_Runtime_Foundation":
            errors.append(f"expected branch 7_Runtime_Foundation, got {branch}")

    return errors


def run_baseline_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.slides_service import SlidesService  # noqa: PLC0415

    service = SlidesService()
    output = service.generate_deck(
        "Executive context. Customer problem. Current workflow friction. Proposed offline slides solution. "
        "Implementation milestones. Operator readiness. Final recommendation.",
        template_id="business_clean",
        session_id="rf2_1_smoke_session",
        task_id="rf2_1_smoke_task",
        owner_user_id="user_local_default",
        source_refs=(
            {
                "source_id": "rf2_1_inventory",
                "source_type": "operator_instruction",
                "role": "primary_source",
            },
        ),
    )

    errors: list[str] = []
    payload = output.artifact_content
    if not payload.startswith(b"PK"):
        errors.append("generated PPTX payload does not start with ZIP magic PK")

    names: set[str] = set()
    slide_entries: list[str] = []
    first_slide_contains_context = False
    media_entries: list[str] = []

    try:
        with zipfile.ZipFile(BytesIO(payload), "r") as pptx:
            names = set(pptx.namelist())
            slide_entries = sorted(
                name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )
            media_entries = sorted(name for name in names if name.startswith("ppt/media/"))
            first_slide = pptx.read("ppt/slides/slide1.xml").decode("utf-8")
            first_slide_contains_context = "Executive context" in first_slide or "Slide 1" in first_slide
    except Exception as exc:  # noqa: BLE001
        errors.append(f"failed to inspect generated PPTX zip: {exc}")

    for part in CORE_PPTX_PARTS:
        if part not in names:
            errors.append(f"generated PPTX is missing core part: {part}")

    if len(slide_entries) != output.slide_count:
        errors.append(f"slide XML count {len(slide_entries)} does not match service slide_count {output.slide_count}")
    if output.slide_count < 5:
        errors.append(f"expected at least 5 generated slides, got {output.slide_count}")
    if not output.outline:
        errors.append("service returned empty outline")
    if not output.plan.slides:
        errors.append("service returned empty plan")
    if output.template_id != "business_clean":
        errors.append(f"expected business_clean template, got {output.template_id}")
    if not any(slide.media_assets for slide in output.plan.slides):
        errors.append("expected at least one generated media asset in the plan")
    if not output.source_grounding_metadata:
        errors.append("expected source grounding metadata")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "current_generator_grade": "baseline_deterministic_not_kimi_grade",
        "kimi_grade_supported": False,
        "product_grade_supported": False,
        "whole_project_kimi_level_supported": False,
        "product_loop_grade": "baseline_inventory_not_kimi_level_project",
        "approved_plan_runtime_proven": False,
        "provenance_artifact_emitted": False,
        "persistent_task_event_stream_proven": False,
        "visual_qa_runtime_proven": False,
        "slide_count": output.slide_count,
        "summary_text": output.summary_text,
        "template_id": output.template_id,
        "payload_starts_with_pk": payload.startswith(b"PK"),
        "payload_size_bytes": len(payload),
        "core_parts_present": sorted(part for part in CORE_PPTX_PARTS if part in names),
        "slide_xml_count": len(slide_entries),
        "media_entry_count": len(media_entries),
        "has_media_assets_in_plan": any(slide.media_assets for slide in output.plan.slides),
        "has_source_grounding_metadata": bool(output.source_grounding_metadata),
        "first_slide_contains_context": first_slide_contains_context,
        "outline_title_sample": output.outline[0].title if output.outline else "",
    }


def build_capabilities(marker_report: dict[str, bool], smoke: dict[str, Any]) -> list[Capability]:
    baseline_ready = [
        Capability(
            "deterministic_pptx_generation_from_source_text",
            "baseline_runtime_ready"
            if smoke["status"] == "ready" and marker_report["slides_service_generate_deck"] and marker_report["pptx_from_plan"]
            else "not_ready",
            ["SlidesService.generate_deck", "generate_pptx_from_plan", "OpenXML PPTX smoke"],
            "RF2.2 should reuse this generator but must not claim Kimi-grade output.",
        ),
        Capability(
            "local_templates_and_layouts",
            "baseline_runtime_ready" if smoke["status"] == "ready" and marker_report["deterministic_zip_timestamp"] else "not_ready",
            ["business_clean template smoke", "deterministic ZIP timestamp marker"],
            "RF2.5 should harden adaptive/template metadata and product-quality layout gates.",
        ),
        Capability(
            "presentation_catalog_and_plan_read_api",
            "baseline_runtime_ready"
            if all(
                marker_report[name]
                for name in (
                    "presentation_list_route",
                    "presentation_versions_route",
                    "presentation_current_plan_route",
                    "presentation_version_plan_route",
                    "presentation_plan_diff_route",
                    "presentation_catalog_service",
                )
            )
            else "not_ready",
            ["presentations routes", "PresentationCatalogService", "plan and diff response schemas"],
            "RF2.2/RF2.3 can build on existing read paths.",
        ),
        Capability(
            "frontend_plan_editor_surface",
            "baseline_runtime_ready"
            if marker_report["frontend_plan_editor"] and marker_report["frontend_plan_editor_e2e"]
            else "not_ready",
            ["SlidesPlanEditorPanel", "slides-plan-editor-smoke.spec.ts"],
            "RF2.7 can build on the existing plan editor surface.",
        ),
    ]

    partial = [
        Capability(
            "approved_plan_generation_path",
            "partial_runtime",
            ["PresentationPlan exists", "generate_pptx_from_plan exists", "explicit approved-plan API/runtime path still needs RF2.2 wiring"],
            "RF2.2",
        ),
        Capability(
            "plan_snapshot_and_retry_lifecycle",
            "partial_runtime" if marker_report["plan_snapshot_service"] and marker_report["deck_revision_service"] else "not_ready",
            ["PresentationPlanSnapshotService", "DeckRevisionService", "saved-plan retry lifecycle still needs runtime path"],
            "RF2.3/RF2.4",
        ),
        Capability(
            "artifact_history_and_provenance_for_generated_decks",
            "partial_runtime",
            ["artifact registration exists elsewhere in project", "slides provenance manifest remains contract-only for emitted downloadable manifest"],
            "RF2.6",
        ),
    ]

    gaps = [
        Capability("kimi_grade_slides_quality", "product_gap", ["baseline smoke is not a Kimi-like quality gate"], "RF2.2+ product gates"),
        Capability("product_grade_layout_quality", "product_gap", ["no rich deck visual QA or layout quality runtime is proven"], "RF2.5/RF2.7"),
        Capability("llm_backed_local_gigachat_plan_generation", "product_gap", ["RF2.1 uses deterministic source text planning only"], "future RF2 step"),
        Capability("whole_project_kimi_level_product_loop", "product_gap", ["source intake, planning, editing, rendering, provenance, QA, retry, and operator gates are not proven as one product loop"], "RF2.2+ / RF3"),
    ]

    contract_only = [
        Capability("slides_task_event_stream_persistence", "contract_only", ["S4 contract exists, concrete runtime event persistence is not RF2.1 scope"], "RF2.3"),
        Capability("slides_provenance_manifest_artifact", "contract_only", ["S7 contract exists, emitted downloadable provenance manifest is future runtime work"], "RF2.6"),
        Capability("visual_qa_runtime", "contract_only", ["S10 visual QA planning exists, no multimodal runtime in RF2.1"], "future optional runtime"),
        Capability("browser_evidence_runtime", "contract_only", ["S8 browser evidence contract exists, no autonomous browser runtime in RF2.1"], "future optional runtime"),
    ]

    return baseline_ready + partial + gaps + contract_only


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready=require_ready)
    marker_report = collect_marker_report(repo_root)
    smoke = run_baseline_smoke(repo_root) if not static_errors else {"status": "skipped", "errors": ["static checks failed"]}
    capabilities = build_capabilities(marker_report, smoke)
    errors = list(static_errors)
    errors.extend(smoke.get("errors", []))

    return {
        "mode": "slides-runtime-capability-inventory",
        "phase": "RF2",
        "checkpoint": "RF2.1",
        "network_required": False,
        "runtime_changed_by_rf2_1": False,
        "dependency_versions_changed_by_rf2_1": False,
        "dockerfiles_changed_by_rf2_1": False,
        "llm_topology_changed_by_rf2_1": False,
        "browser_runtime_changed_by_rf2_1": False,
        "frontend_runtime_changed_by_rf2_1": False,
        "current_generator_grade": smoke.get("current_generator_grade", "unknown"),
        "product_loop_grade": smoke.get("product_loop_grade", "baseline_inventory_not_kimi_level_project"),
        "kimi_grade_supported": smoke.get("kimi_grade_supported", False),
        "product_grade_supported": smoke.get("product_grade_supported", False),
        "whole_project_kimi_level_supported": smoke.get("whole_project_kimi_level_supported", False),
        "system_quality_gaps": [
            "source_intake_and_document_understanding_not_quality_gated",
            "local_gigachat_planning_not_proven_in_rf2_1",
            "plan_editor_not_connected_to_full_generation_lifecycle",
            "renderer_layout_quality_not_kimi_grade",
            "provenance_manifest_not_emitted_as_downloadable_artifact",
            "visual_qa_runtime_not_implemented",
            "retry_lifecycle_not_end_to_end",
            "operator_event_stream_not_persisted_for_slides_runtime",
        ],
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "marker_report": marker_report,
        "baseline_smoke": smoke,
        "capabilities": [asdict(item) for item in capabilities],
        "summary": {
            "baseline_runtime_ready": sum(1 for item in capabilities if item.status == "baseline_runtime_ready"),
            "partial_runtime": sum(1 for item in capabilities if item.status == "partial_runtime"),
            "product_gap": sum(1 for item in capabilities if item.status == "product_gap"),
            "contract_only": sum(1 for item in capabilities if item.status == "contract_only"),
            "not_ready": sum(1 for item in capabilities if item.status == "not_ready"),
        },
        "next_recommended_step": "RF2.2 — Minimal deterministic PPTX generation from approved plan",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio RF2.1 slides runtime capability inventory and baseline smoke.")
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
