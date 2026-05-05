#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "docs/codex/K6_END_TO_END_KIMI_LIKE_WORKFLOW.md",
    "backend/app/services/k_phase/end_to_end_workflow.py",
    "scripts/kw_k6_end_to_end_workflow_check.py",
    "backend/tests/smoke/test_k6_end_to_end_workflow.py",
)
EXPECTED_BASE_AFTER_K5 = "fafdfd0840428f2d006da19c3c56eec64701168c"


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing K6 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch is not None and branch not in ("8_K_Phase", "9_Product_Release_Hardening"):
            errors.append(f"expected branch 8_K_Phase or 9_Product_Release_Hardening, got {branch}")
    return errors


def run_runtime_smoke(repo_root: Path) -> dict[str, Any]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services.k_phase.end_to_end_workflow import (
        K6EndToEndWorkflowRequest,
        build_k6_capabilities_report,
        run_k6_end_to_end_workflow,
        validate_k6_end_to_end_result,
    )

    source_text = (
        "Offline executive reporting requires source-grounded presentations. "
        "Local GigaChat planning creates an editable outline before rendering. "
        "Operators approve the plan before generation. "
        "Renderer quality bounds dense content and selects local templates. "
        "Visual QA inspects local PPTX OOXML for layout risk. "
        "Source-to-slide provenance links every slide to bounded evidence. "
        "The final workflow must remain offline and avoid cloud fallback."
    )
    result = run_k6_end_to_end_workflow(
        K6EndToEndWorkflowRequest(
            source_text=source_text,
            source_refs=(
                {
                    "kind": "document",
                    "source_id": "k6_operator_memo_001",
                    "title": "K6 operator memo",
                    "role": "primary_source",
                    "locator": "memo.md#k6-workflow",
                    "source_file_id": "file_k6_operator_memo_001",
                    "derived_content_id": "derived_text_k6_001",
                    "checksum_sha256": "abc123",
                },
            ),
            target_slide_count=7,
            artifact_filename="k6-end-to-end-smoke.pptx",
            session_id="k6_smoke_session",
            task_id="k6_smoke_task",
            presentation_id="k6_smoke_presentation",
        )
    )
    capabilities = build_k6_capabilities_report()
    validation_errors = validate_k6_end_to_end_result(result)
    metadata = result.safe_metadata
    encoded_metadata = json.dumps(metadata, ensure_ascii=False, sort_keys=True).lower()
    errors: list[str] = list(validation_errors)

    if metadata.get("checkpoint") != "K6":
        errors.append("K6 metadata checkpoint mismatch")
    if metadata.get("status") != "ready_for_operator_delivery":
        errors.append(f"K6 workflow did not become deliverable: {metadata.get('status')}")
    if metadata.get("end_to_end_kimi_like_workflow_supported") is not True:
        errors.append("K6 end-to-end workflow not reported as supported")
    if result.planning_result.safe_metadata.get("checkpoint") != "K1":
        errors.append("K6 did not integrate K1 planning result")
    if result.plan_editor_result.safe_metadata.get("checkpoint") != "K2":
        errors.append("K6 did not integrate K2 plan editor approval")
    if result.renderer_quality_result.safe_metadata.get("checkpoint") != "K3":
        errors.append("K6 did not integrate K3 renderer quality")
    if result.visual_qa_result.safe_metadata.get("checkpoint") != "K4":
        errors.append("K6 did not integrate K4 visual QA")
    if result.provenance_result.safe_metadata.get("checkpoint") != "K5":
        errors.append("K6 did not integrate K5 provenance")
    if result.provenance_result.coverage.coverage_status != "complete":
        errors.append("K6 provenance coverage is not complete")
    if result.visual_qa_result.status not in {"passed", "needs_operator_review"}:
        errors.append(f"K6 visual QA status is not acceptable: {result.visual_qa_result.status}")
    if result.operator_review.decision != "approve":
        errors.append("K6 operator gate did not approve the smoke workflow")
    if result.render_result.size_bytes <= 0:
        errors.append("K6 PPTX artifact is empty")
    if not all(slide.citations for slide in result.provenance_result.plan.slides):
        errors.append("K6 every slide must have a citation after K5")
    if not result.manifest.get("source_to_slide_provenance"):
        errors.append("K6 manifest missing K5 source-to-slide provenance")
    if result.manifest.get("k6_workflow", {}).get("checkpoint") != "K6":
        errors.append("K6 manifest missing K6 workflow section")
    if any(gate.status != "passed" for gate in result.gates):
        errors.append("K6 workflow gates did not all pass")
    if metadata.get("network_required") is not False:
        errors.append("K6 must remain offline/local with network_required=false")
    if "offline executive reporting requires" in encoded_metadata:
        errors.append("K6 safe metadata contains raw source text")
    if capabilities.get("api_endpoint_added_by_k6") is not False:
        errors.append("K6 must not add API endpoint")
    if capabilities.get("db_schema_migration_added_by_k6") is not False:
        errors.append("K6 must not add DB schema migration")
    if capabilities.get("frontend_runtime_changed_by_k6") is not False:
        errors.append("K6 must not change frontend runtime")
    if capabilities.get("dependency_versions_changed_by_k6") is not False:
        errors.append("K6 must not change dependency versions")
    if capabilities.get("dockerfiles_changed_by_k6") is not False:
        errors.append("K6 must not change Dockerfiles")
    if capabilities.get("cloud_llm_added_by_k6") is not False or capabilities.get("cloud_vision_added_by_k6") is not False:
        errors.append("K6 must not add cloud LLM or cloud vision")
    if capabilities.get("kimi_level_claimed_by_k6") is not False:
        errors.append("K6 must not claim full Kimi-level")
    if metadata.get("whole_project_kimi_level_supported") is not False:
        errors.append("K6 must not claim whole-project Kimi-level")

    return {
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "end_to_end_kimi_like_workflow_supported": metadata.get("end_to_end_kimi_like_workflow_supported") is True,
        "source_to_pptx_workflow_supported": metadata.get("source_to_pptx_workflow_supported") is True,
        "k1_planning_integrated": metadata.get("k1_planning_integrated") is True,
        "k2_plan_editor_approval_integrated": metadata.get("k2_plan_editor_approval_integrated") is True,
        "k3_renderer_quality_integrated": metadata.get("k3_renderer_quality_integrated") is True,
        "k4_visual_qa_integrated": metadata.get("k4_visual_qa_integrated") is True,
        "k5_source_to_slide_provenance_integrated": metadata.get("k5_source_to_slide_provenance_integrated") is True,
        "operator_gate_supported": metadata.get("operator_gate_supported") is True,
        "downloadable_artifact_supported": metadata.get("downloadable_artifact_supported") is True,
        "safe_manifest_supported": metadata.get("safe_manifest_supported") is True,
        "offline_intranet_default_supported": metadata.get("offline_intranet_default_supported") is True,
        "workflow_status": metadata.get("status"),
        "slide_count": result.render_result.slide_count,
        "artifact_size_bytes": result.render_result.size_bytes,
        "visual_qa_status": result.visual_qa_result.status,
        "operator_decision": result.operator_review.decision,
        "k5_coverage_status": result.provenance_result.coverage.coverage_status,
        "gate_count": len(result.gates),
        "passed_gate_count": sum(1 for gate in result.gates if gate.status == "passed"),
        "manifest_digest": metadata.get("manifest_digest"),
        "api_endpoint_added_by_k6": False,
        "db_schema_migration_added_by_k6": False,
        "frontend_runtime_changed_by_k6": False,
        "dependency_versions_changed_by_k6": False,
        "dockerfiles_changed_by_k6": False,
        "cloud_llm_added_by_k6": False,
        "cloud_vision_added_by_k6": False,
        "kimi_level_claimed_by_k6": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
    }


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    static_errors = collect_static_errors(repo_root, require_ready)
    runtime = run_runtime_smoke(repo_root) if not static_errors else {"status": "failed", "errors": []}
    errors = static_errors + list(runtime.get("errors", []))
    report = {
        "checkpoint": "K6",
        "schema_version": "k6.end_to_end_kimi_like_workflow.check.v1",
        "expected_base_after_k5": EXPECTED_BASE_AFTER_K5,
        **runtime,
        "errors": errors,
        "status": "ready" if not errors and runtime.get("status") == "ready" else "failed",
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check K6 end-to-end Kimi-like workflow runtime readiness.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repo_root.resolve(), args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"K6 end-to-end workflow status: {report['status']}")
        for key in ("workflow_status", "slide_count", "artifact_size_bytes", "visual_qa_status", "operator_decision", "k5_coverage_status"):
            print(f"{key}: {report.get(key)}")
        if report.get("errors"):
            print("errors:")
            for error in report["errors"]:
                print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
