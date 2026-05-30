#!/usr/bin/env python3
"""KR-7H.9 minimal PresentationIR mapping temporary PPTX smoke checker."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[1]
if str(REPO_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_FOR_IMPORTS))

from backend.app.services.slides_service import (
    OfflineEvidenceIndexBuilder,
    OfflineSourceIngestionEngine,
    PresentationIRPlannerFoundation,
    PresentationIRPlannerRequest,
    build_renderer_worker_dry_run_report,
)

SCHEMA_VERSION = "presentation_renderer_worker_minimal_ir_mapping_smoke.v1"
EXPECTED_VERSION = "4.0.1"
INTERNAL_REGISTRY_MARKERS = (
    "packages.applied-caas",
    "applied-caas-gateway",
    "internal.api.openai.org/artifactory",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _node_available() -> bool:
    return shutil.which("node") is not None


def _npm_available() -> bool:
    return shutil.which("npm") is not None


def _run_json(command: list[str], *, cwd: Path, stdin_payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any] | None, str]:
    completed = subprocess.run(
        command,
        input=None if stdin_payload is None else json.dumps(stdin_payload, ensure_ascii=False),
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = None
    diagnostics = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    return completed.returncode, payload, diagnostics


def _worker_dependency_tree_ready(worker_root: Path) -> bool:
    return (worker_root / "node_modules" / "pptxgenjs" / "package.json").is_file()


def _ensure_npm_install(worker_root: Path, problems: list[str]) -> None:
    if not _npm_available():
        problems.append("npm executable is required for KR-7H.9 minimal mapping check")
        return
    if _worker_dependency_tree_ready(worker_root):
        return
    completed = subprocess.run(
        ["npm", "ci", "--ignore-scripts", "--audit=false", "--fund=false", "--silent"],
        cwd=worker_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        problems.append(f"npm ci --prefix renderer_worker failed: {completed.stdout}{completed.stderr}")


def _validate_lockfile(repo_root: Path, problems: list[str]) -> None:
    lock_path = repo_root / "renderer_worker" / "package-lock.json"
    text = _read(lock_path)
    for marker in INTERNAL_REGISTRY_MARKERS:
        if marker in text:
            problems.append(f"renderer_worker/package-lock.json contains environment-specific registry marker {marker!r}")
    lock = json.loads(text)
    packages = lock.get("packages") if isinstance(lock, dict) else {}
    root = packages.get("") if isinstance(packages, dict) else {}
    dependency = packages.get("node_modules/pptxgenjs") if isinstance(packages, dict) else {}
    if not isinstance(root, dict) or root.get("dependencies", {}).get("pptxgenjs") != EXPECTED_VERSION:
        problems.append("renderer_worker/package-lock.json root dependency must pin pptxgenjs@4.0.1")
    if not isinstance(dependency, dict) or dependency.get("version") != EXPECTED_VERSION:
        problems.append("renderer_worker/package-lock.json must lock node_modules/pptxgenjs version 4.0.1")


def _source_backed_dry_run_payload() -> dict[str, Any]:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Retention\n\nCustomer retention improved after support automation.\n\n# Risk\n\nDeployment risk decreased after rollout automation.",
        source_id="src_renderer_kr7h9",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    planner_result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h9",
            title="Support automation results",
            objective="Support automation retention risk",
            slide_count=4,
            required_sections=("retention", "risk"),
            require_evidence=True,
        ),
        index,
    )
    if planner_result.presentation_ir is None:
        raise AssertionError("KR-7H.9 checker could not build source-backed PresentationIR")
    dry_run = build_renderer_worker_dry_run_report(planner_result.presentation_ir, request_id="req_kr7h9_checker")
    if dry_run.status != "ready":
        raise AssertionError(f"KR-7H.9 checker dry-run should be ready, got {dry_run.status}")
    return dry_run.as_dict()


def _validate_result(payload: dict[str, Any], problems: list[str], *, label: str) -> None:
    expected = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "dependency_name": "pptxgenjs",
        "expected_dependency_version": EXPECTED_VERSION,
        "dependency_available": True,
        "dependency_version": EXPECTED_VERSION,
        "minimal_ir_mapping_smoke_implemented": True,
        "renderer_input_schema_version": "presentation_renderer_worker_input.v1",
        "input_status": "ready",
        "mapped_fields": ["title", "body"],
        "mapped_block_types": ["text"],
        "single_slide_smoke_executed": True,
        "multi_slide_smoke_executed": True,
        "single_slide_pptx_written": True,
        "single_slide_pptx_deleted": True,
        "single_slide_file_size_nonzero": True,
        "multi_slide_pptx_written": True,
        "multi_slide_pptx_deleted": True,
        "multi_slide_file_size_nonzero": True,
        "temporary_directory_removed": True,
        "title_body_mapping_implemented": True,
        "chart_mapping_implemented": False,
        "table_mapping_implemented": False,
        "image_mapping_implemented": False,
        "theme_mapping_implemented": False,
        "professional_layout_engine_implemented": False,
        "user_prompt_passthrough_allowed": False,
        "presentation_ir_mapping_implemented": True,
        "production_pptx_output_implemented": False,
        "renderer_runtime_implemented": False,
        "persistent_artifact_written": False,
        "filesystem_output_written": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
        "libreoffice_executed": False,
        "visual_qa_executed": False,
        "output_mode": "temporary_minimal_ir_mapping_smoke_only",
    }
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value:
            problems.append(f"{label}: expected {key}={expected_value!r}, got {payload.get(key)!r}")
    if payload.get("issues") != []:
        problems.append(f"{label}: expected no issues, got {payload.get('issues')!r}")
    if not isinstance(payload.get("mapped_slide_count"), int) or payload["mapped_slide_count"] < 2:
        problems.append(f"{label}: expected at least two mapped slides for multi-slide smoke")
    if not isinstance(payload.get("mapped_slide_ids"), list) or len(payload["mapped_slide_ids"]) < 2:
        problems.append(f"{label}: expected stable mapped_slide_ids for multi-slide smoke")
    if not isinstance(payload.get("single_slide_file_size_bytes"), int) or payload["single_slide_file_size_bytes"] <= 0:
        problems.append(f"{label}: single-slide temporary PPTX size must be positive")
    if not isinstance(payload.get("multi_slide_file_size_bytes"), int) or payload["multi_slide_file_size_bytes"] <= 0:
        problems.append(f"{label}: multi-slide temporary PPTX size must be positive")
    for action in ("persist_pptx_artifact", "run_libreoffice_pdf_export", "write_artifact_bundle", "write_proof_bundle", "map_charts_tables_images"):
        if action not in payload.get("blocked_runtime_actions", []):
            problems.append(f"{label}: blocked_runtime_actions missing {action}")
    for non_goal in ("no_persistent_pptx_artifact", "no_libreoffice_execution", "no_artifact_bundle_storage", "no_charts_tables_images_mapping"):
        if non_goal not in payload.get("non_goals", []):
            problems.append(f"{label}: non_goals missing {non_goal}")


def check(repo_root: Path) -> dict[str, Any]:
    problems: list[str] = []
    worker_root = repo_root / "renderer_worker"
    script = worker_root / "kw_renderer_worker_minimal_ir_mapping_smoke.mjs"
    if not script.is_file():
        problems.append("renderer_worker/kw_renderer_worker_minimal_ir_mapping_smoke.mjs is missing")
        return {"schema_version": "kw_renderer_worker_minimal_ir_mapping_check.v1", "status": "blocked", "problems": problems}
    if not _node_available():
        problems.append("node executable is required for KR-7H.9 minimal mapping check")
        return {"schema_version": "kw_renderer_worker_minimal_ir_mapping_check.v1", "status": "blocked", "problems": problems}

    _validate_lockfile(repo_root, problems)
    syntax = subprocess.run(["node", "--check", script.name], cwd=worker_root, text=True, capture_output=True, check=False)
    if syntax.returncode != 0:
        problems.append(f"node --check renderer_worker/{script.name} failed: {syntax.stdout}{syntax.stderr}")
    if not problems:
        _ensure_npm_install(worker_root, problems)
    if not problems:
        code, fixture_result, diagnostics = _run_json(["npm", "run", "pptxgenjs:minimal-ir-smoke", "--silent"], cwd=worker_root)
        if code != 0 or not isinstance(fixture_result, dict):
            problems.append(f"npm run pptxgenjs:minimal-ir-smoke --prefix renderer_worker did not return ready JSON: {diagnostics}")
        else:
            _validate_result(fixture_result, problems, label="fixture")
    if not problems:
        dry_run_payload = _source_backed_dry_run_payload()
        code, stdin_result, diagnostics = _run_json(["node", script.name, "--json", "--stdin"], cwd=worker_root, stdin_payload=dry_run_payload)
        if code != 0 or not isinstance(stdin_result, dict):
            problems.append(f"renderer_worker minimal mapping stdin smoke did not return ready JSON: {diagnostics}")
        else:
            _validate_result(stdin_result, problems, label="source_backed_dry_run")

    status = "ready" if not problems else "blocked"
    return {"schema_version": "kw_renderer_worker_minimal_ir_mapping_check.v1", "status": status, "problems": problems}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = check(Path(args.repo_root).resolve())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"kw_renderer_worker_minimal_ir_mapping_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
