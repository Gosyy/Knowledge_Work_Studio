#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

CHECKPOINT = "S1"
SCHEMA_VERSION = "s1.kimi_slides_class_gap_dossier.v1"
EXPECTED_BASE_AFTER_P10_10 = "f369412ba284f5f149a81ab42cb25b45b74bfaa4"
REQUIRED_FILES = (
    "docs/codex/P10_11_FINAL_OPERATOR_RELEASE_CLOSURE.md",
    "docs/codex/S_PHASE_KIMI_SLIDES_CLASS_ROADMAP.md",
    "docs/codex/S1_KIMI_SLIDES_CLASS_GAP_DOSSIER.md",
    "scripts/kw_p10_11_final_operator_release_closure.py",
    "scripts/kw_s1_kimi_slides_gap_check.py",
    "backend/tests/smoke/test_s1_kimi_slides_gap.py",
)
S_PHASE_IDS = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10")
REQUIRED_CAPABILITY_IDS = (
    "outline_first_workflow",
    "editable_plan_before_generation",
    "adaptive_deck_modes",
    "native_table_chart_diagram_rendering",
    "template_master_ingestion",
    "image_screenshot_to_slide_workflow",
    "offline_research_citations",
    "conversational_edit_loop",
    "render_based_visual_qa",
    "expanded_kimi_style_benchmark",
)


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def digest_payload(payload: Any) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing S1 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_10:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_P10_10, head)
            if ancestry is False:
                errors.append(f"expected P10-10 baseline {EXPECTED_BASE_AFTER_P10_10} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P10-10 ancestry for {EXPECTED_BASE_AFTER_P10_10}..{head}")
    return errors


def run_p10_11(repo_root: Path, require_ready: bool) -> tuple[dict[str, Any] | None, str, str, int]:
    command = [sys.executable, "scripts/kw_p10_11_final_operator_release_closure.py", "--repo-root", str(repo_root), "--json"]
    if require_ready:
        command.append("--require-ready")
    result = subprocess.run(command, cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    payload: dict[str, Any] | None = None
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = None
    return payload, result.stdout, result.stderr, result.returncode


def capability_matrix() -> list[dict[str, Any]]:
    return [
        {
            "capability_id": "outline_first_workflow",
            "current_state": "partial_contract_foundation",
            "target_state": "frontend-visible outline generation, edit, approval, and retry from saved plan",
            "phase": "S2",
            "acceptance": "operator can generate outline, edit it, approve it, and generate PPTX from the approved plan",
        },
        {
            "capability_id": "editable_plan_before_generation",
            "current_state": "partial_backend_foundation",
            "target_state": "first-class plan editor with provenance from source to plan to slide",
            "phase": "S2",
            "acceptance": "approved plan is persisted and can be used for deterministic regeneration",
        },
        {
            "capability_id": "adaptive_deck_modes",
            "current_state": "case-specific hardening exists but not complete mode registry",
            "target_state": "deck-mode registry with storyline skeletons and slide archetypes",
            "phase": "S3",
            "acceptance": "board, architecture, status, decision matrix, and long-document explainer modes select appropriate slide archetypes",
        },
        {
            "capability_id": "native_table_chart_diagram_rendering",
            "current_state": "improved by P9/P10 but still benchmark-limited",
            "target_state": "PPTX-native decision matrices, risk tables, topology diagrams, KPI charts, and roadmaps",
            "phase": "S4",
            "acceptance": "structured data inputs render as editable PPTX tables/charts/diagrams rather than raw text",
        },
        {
            "capability_id": "template_master_ingestion",
            "current_state": "not first-class",
            "target_state": "offline PPTX template/theme/master parsing and slide archetype mapping",
            "phase": "S5",
            "acceptance": "uploaded template controls theme colors, fonts, masters, and generated deck layout mapping",
        },
        {
            "capability_id": "image_screenshot_to_slide_workflow",
            "current_state": "future heavy-runtime workflow",
            "target_state": "local OCR/vision-assisted reconstruction into editable slide components where possible",
            "phase": "S6",
            "acceptance": "screenshot/image evidence can become a cited, editable slide draft without cloud vision dependency",
        },
        {
            "capability_id": "offline_research_citations",
            "current_state": "source provenance exists for uploaded/internal sources",
            "target_state": "citation workflow from uploaded docs, browser evidence, and intranet/local knowledge base",
            "phase": "S7",
            "acceptance": "slides show useful citations without hidden public web dependency in production mode",
        },
        {
            "capability_id": "conversational_edit_loop",
            "current_state": "retry/saved-plan foundations exist but not full conversational editing",
            "target_state": "operator can request scoped edits over saved plans and generated decks",
            "phase": "S8",
            "acceptance": "edits like shorten, executive rewrite, add risk slide, or convert table to matrix are plan-aware and auditable",
        },
        {
            "capability_id": "render_based_visual_qa",
            "current_state": "semantic/heuristic QA exists; P10 revealed human-visible overlap gaps",
            "target_state": "rendered-slide image QA for overlap, clipping, tiny text, table overflow, and title/body collision",
            "phase": "S9",
            "acceptance": "visual QA catches the kind of architecture slide overlap that triggered P10-9",
        },
        {
            "capability_id": "expanded_kimi_style_benchmark",
            "current_state": "five golden cases plus human review workflow",
            "target_state": "12+ Kimi Slides-class benchmark scenarios with human review thresholds",
            "phase": "S10",
            "acceptance": "selected offline/intranet slide workflows pass expanded benchmark without Kimi-level overclaim",
        },
    ]


def phase_roadmap() -> list[dict[str, str]]:
    return [
        {"phase": "S1", "title": "Kimi Slides-class gap dossier", "goal": "define capability gaps and evidence boundaries"},
        {"phase": "S2", "title": "Outline-first frontend workflow", "goal": "make outline/edit/approve/retry first-class"},
        {"phase": "S3", "title": "Adaptive deck modes", "goal": "use mode-specific storyline and slide archetype registries"},
        {"phase": "S4", "title": "Native table/chart/diagram rendering", "goal": "turn structured data into editable PPTX visuals"},
        {"phase": "S5", "title": "Template and master ingestion", "goal": "support offline brand/template-driven deck generation"},
        {"phase": "S6", "title": "Image and screenshot to slide workflow", "goal": "reconstruct visual evidence into editable slides where possible"},
        {"phase": "S7", "title": "Offline research citations", "goal": "support cited decks from uploaded/internal/intranet sources"},
        {"phase": "S8", "title": "Conversational edit loop", "goal": "apply auditable plan-aware slide edits"},
        {"phase": "S9", "title": "Render-based visual QA", "goal": "catch real rendered layout defects"},
        {"phase": "S10", "title": "Expanded Kimi-style benchmark", "goal": "validate selected Kimi Slides-class workflows with human review"},
    ]


def build_report(repo_root: Path, artifacts_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    p10_11_report: dict[str, Any] | None = None
    if not errors:
        p10_11_report, stdout, stderr, returncode = run_p10_11(repo_root, require_ready)
        if returncode != 0:
            errors.append(f"P10-11 closure failed during S1 gap dossier with exit code {returncode}: {stderr.strip() or stdout.strip()[:500]}")
        if p10_11_report is None:
            errors.append("S1 could not parse P10-11 closure JSON output")
        elif p10_11_report.get("status") != "ready":
            errors.append(f"P10-11 closure is not ready during S1: {p10_11_report.get('status')!r}")
        elif p10_11_report.get("project_release_status_after_p10_11") != "approved_for_operator_handoff":
            errors.append("S1 requires P10-11 operator handoff closure to be ready")
    if p10_11_report is None:
        p10_11_report = {}
    matrix = capability_matrix()
    roadmap = phase_roadmap()
    matrix_ids = {item["capability_id"] for item in matrix}
    missing_capabilities = [cap for cap in REQUIRED_CAPABILITY_IDS if cap not in matrix_ids]
    if missing_capabilities:
        errors.append("missing S1 capability gap entries: " + ", ".join(missing_capabilities))
    roadmap_ids = {item["phase"] for item in roadmap}
    missing_phases = [phase for phase in S_PHASE_IDS if phase not in roadmap_ids]
    if missing_phases:
        errors.append("missing S-phase roadmap entries: " + ", ".join(missing_phases))
    ready = not errors
    report = {
        "mode": "s1-kimi-slides-class-gap-dossier",
        "phase": "S-phase Kimi Slides-class workflow quality track",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_10": EXPECTED_BASE_AFTER_P10_10,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "p10_11_closure_digest": digest_payload(p10_11_report) if p10_11_report else None,
        "p10_release_status_required_for_s_phase": "approved_for_operator_handoff",
        "s_phase_track_opened_by_s1": bool(ready),
        "s_phase_count": len(roadmap),
        "s_phase_ids": [item["phase"] for item in roadmap],
        "kimi_slides_class_goal_declared": True,
        "kimi_level_claimed_by_s1": False,
        "whole_project_kimi_level_supported": False,
        "kimi_slides_class_parity_claim_supported_by_s1": False,
        "offline_intranet_constraint_preserved_by_s1": True,
        "server3_local_intranet_route_verified_by_s1": False,
        "public_api_dev_gigachat_evidence_remains_completion_evidence_not_server3_proof": True,
        "capability_gap_count": len(matrix),
        "capability_gap_ids": [item["capability_id"] for item in matrix],
        "capability_gap_matrix": matrix,
        "s_phase_roadmap": roadmap,
        "first_execution_phase_after_s1": "S2",
        "next_recommended_step": "S2 - implement outline-first frontend workflow with editable plan, approved plan persistence, and retry from saved plan.",
        "npm_audit_fix_force_run_by_s1": False,
        "api_endpoint_added_by_s1": False,
        "db_schema_migration_added_by_s1": False,
        "frontend_runtime_changed_by_s1": False,
        "dependency_versions_changed_by_s1": False,
        "dockerfiles_changed_by_s1": False,
        "cloud_llm_added_by_s1": False,
        "cloud_vision_added_by_s1": False,
        "network_required_for_s1": False,
    }
    report["s1_gap_dossier_digest"] = digest_payload(report)
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out = artifacts_dir / "s1_kimi_slides_class_gap_dossier.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        report["s1_gap_dossier_file"] = str(out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KW Studio S1 Kimi Slides-class capability gap dossier.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repo_root.resolve(), args.artifacts_dir.resolve() if args.artifacts_dir else None, args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"S1 Kimi Slides-class gap dossier: {report['status']}")
        print(f"S phases: {report['s_phase_count']}")
        print(f"capability gaps: {report['capability_gap_count']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
