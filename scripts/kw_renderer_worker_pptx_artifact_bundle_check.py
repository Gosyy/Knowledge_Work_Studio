#!/usr/bin/env python3
"""KR-7H.10 renderer worker persistent PPTX artifact bundle contract checker."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.services.slides_service import (
    OfflineEvidenceIndexBuilder,
    OfflineSourceIngestionEngine,
    PresentationIRPlannerFoundation,
    PresentationIRPlannerRequest,
    build_renderer_worker_dry_run_report,
)

SCHEMA_VERSION = "presentation_renderer_worker_pptx_artifact_bundle.v1"
RENDER_REPORT_SCHEMA_VERSION = "presentation_renderer_worker_render_report.v1"
EXPECTED_PPTXGENJS_VERSION = "4.0.1"
INTERNAL_REGISTRY_MARKERS = ("packages.applied-caas", "internal.api.openai.org")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _node_available() -> bool:
    return shutil.which("node") is not None


def _npm_available() -> bool:
    return shutil.which("npm") is not None


def _worker_dependency_tree_ready(worker_root: Path) -> bool:
    return (worker_root / "node_modules" / "pptxgenjs" / "package.json").is_file()


def _run_json(command: list[str], *, cwd: Path, stdin_payload: dict[str, object] | None = None) -> tuple[int, dict[str, Any] | None, str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        input=json.dumps(stdin_payload, ensure_ascii=False) if stdin_payload is not None else None,
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


def _validate_lockfile(repo_root: Path, problems: list[str]) -> None:
    lockfile = repo_root / "renderer_worker" / "package-lock.json"
    text = _read(lockfile)
    for marker in INTERNAL_REGISTRY_MARKERS:
        if marker in text:
            problems.append(f"renderer_worker/package-lock.json contains environment-specific registry marker: {marker}")


def _ensure_npm_install(worker_root: Path, problems: list[str]) -> None:
    if not _npm_available():
        problems.append("npm executable is required for KR-7H.10 artifact bundle check")
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


def _source_backed_dry_run_payload() -> dict[str, object]:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Retention\n\nCustomer retention improved after support automation.\n\n# Risk\n\nDeployment risk decreased after rollout automation.",
        source_id="src_renderer_kr7h10_check",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    planner_result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h10_check",
            title="Support automation results",
            objective="Support automation retention risk",
            slide_count=4,
            required_sections=("retention", "risk"),
            require_evidence=True,
        ),
        index,
    )
    if planner_result.presentation_ir is None:
        raise AssertionError("planner_result.presentation_ir is required for KR-7H.10 source-backed smoke")
    dry_run = build_renderer_worker_dry_run_report(planner_result.presentation_ir, request_id="req_kr7h10_check")
    if dry_run.status != "ready":
        raise AssertionError(f"dry-run status must be ready, got {dry_run.status!r}")
    return dry_run.as_dict()


def _validate_bundle_files(result: dict[str, Any], output_dir: Path, problems: list[str], label: str) -> None:
    pptx_basename = result.get("pptx_artifact_basename")
    report_basename = result.get("render_report_basename")
    if not isinstance(pptx_basename, str) or not pptx_basename.endswith(".pptx"):
        problems.append(f"{label}: pptx_artifact_basename must be a .pptx string")
        return
    if not isinstance(report_basename, str) or not report_basename.endswith(".json"):
        problems.append(f"{label}: render_report_basename must be a .json string")
        return
    pptx = output_dir / pptx_basename
    render_report = output_dir / report_basename
    if not pptx.is_file() or pptx.stat().st_size <= 0:
        problems.append(f"{label}: persistent PPTX artifact is missing or empty: {pptx}")
    if not render_report.is_file() or render_report.stat().st_size <= 0:
        problems.append(f"{label}: render report JSON is missing or empty: {render_report}")
        return
    try:
        report = json.loads(render_report.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        problems.append(f"{label}: render report JSON is invalid: {exc}")
        return
    expected_report = {
        "schema_version": RENDER_REPORT_SCHEMA_VERSION,
        "status": "ready",
        "pptx_artifact_basename": pptx_basename,
        "proof_bundle_produced": False,
        "libreoffice_executed": False,
        "visual_qa_executed": False,
    }
    for key, expected in expected_report.items():
        if report.get(key) != expected:
            problems.append(f"{label}: render report {key} expected {expected!r}, got {report.get(key)!r}")


def _validate_result(result: dict[str, Any], output_dir: Path, problems: list[str], label: str) -> None:
    expected_values = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "dependency_name": "pptxgenjs",
        "expected_dependency_version": EXPECTED_PPTXGENJS_VERSION,
        "dependency_available": True,
        "dependency_version": EXPECTED_PPTXGENJS_VERSION,
        "render_report_schema_version": RENDER_REPORT_SCHEMA_VERSION,
        "artifact_bundle_schema_version": SCHEMA_VERSION,
        "persistent_artifact_written": True,
        "persistent_artifact_exists": True,
        "persistent_artifact_file_size_nonzero": True,
        "render_report_written": True,
        "render_report_exists": True,
        "render_report_file_size_nonzero": True,
        "render_report_deterministic": True,
        "artifact_bundle_produced": True,
        "artifact_bundle_verified": True,
        "presentation_ir_mapping_implemented": True,
        "title_body_mapping_implemented": True,
        "chart_mapping_implemented": False,
        "table_mapping_implemented": False,
        "image_mapping_implemented": False,
        "professional_layout_engine_implemented": False,
        "production_pptx_output_implemented": False,
        "proof_bundle_produced": False,
        "libreoffice_executed": False,
        "visual_qa_executed": False,
        "output_mode": "persistent_pptx_artifact_bundle_and_render_report_contract_only",
    }
    for key, expected in expected_values.items():
        if result.get(key) != expected:
            problems.append(f"{label}: {key} expected {expected!r}, got {result.get(key)!r}")
    if result.get("mapped_fields") != ["title", "body"]:
        problems.append(f"{label}: mapped_fields must be ['title', 'body']")
    if result.get("mapped_block_types") != ["text"]:
        problems.append(f"{label}: mapped_block_types must be ['text']")
    if not isinstance(result.get("mapped_slide_ids"), list) or len(result["mapped_slide_ids"]) < 2:
        problems.append(f"{label}: mapped_slide_ids must contain at least two ids")
    if not isinstance(result.get("persistent_artifact_size_bytes"), int) or result["persistent_artifact_size_bytes"] <= 0:
        problems.append(f"{label}: persistent_artifact_size_bytes must be > 0")
    if not isinstance(result.get("render_report_size_bytes"), int) or result["render_report_size_bytes"] <= 0:
        problems.append(f"{label}: render_report_size_bytes must be > 0")
    if result.get("issues") != []:
        problems.append(f"{label}: issues must be empty, got {result.get('issues')!r}")
    _validate_bundle_files(result, output_dir, problems, label)


def check(repo_root: Path) -> dict[str, Any]:
    problems: list[str] = []
    worker_root = repo_root / "renderer_worker"
    script = worker_root / "kw_renderer_worker_pptx_artifact_bundle_smoke.mjs"
    required_files = [
        script,
        repo_root / "scripts" / "kw_renderer_worker_pptx_artifact_bundle_check.py",
        repo_root / "backend" / "tests" / "services" / "test_kr7h_renderer_worker_pptx_artifact_bundle.py",
        worker_root / "package.json",
        worker_root / "package-lock.json",
        worker_root / "CONTRACT.md",
    ]
    for file in required_files:
        if not file.is_file():
            problems.append(f"required file is missing: {file.relative_to(repo_root)}")
    if problems:
        return {"schema_version": "kw_renderer_worker_pptx_artifact_bundle_check.v1", "status": "blocked", "problems": problems}
    if not _node_available():
        problems.append("node executable is required for KR-7H.10 artifact bundle check")
    _validate_lockfile(repo_root, problems)
    syntax = subprocess.run(["node", "--check", script.name], cwd=worker_root, text=True, capture_output=True, check=False)
    if syntax.returncode != 0:
        problems.append(f"node --check renderer_worker/{script.name} failed: {syntax.stdout}{syntax.stderr}")
    if not problems:
        _ensure_npm_install(worker_root, problems)
    if not problems:
        with tempfile.TemporaryDirectory(prefix="kw-kr7h10-check-fixture-") as tmp:
            output_dir = Path(tmp) / "bundle"
            code, result, diagnostics = _run_json([
                "node",
                script.name,
                "--json",
                "--fixture",
                "--output-dir",
                str(output_dir),
            ], cwd=worker_root)
            if code != 0 or not isinstance(result, dict):
                problems.append(f"fixture artifact bundle smoke did not return ready JSON: {diagnostics}")
            else:
                _validate_result(result, output_dir, problems, label="fixture")
    if not problems:
        with tempfile.TemporaryDirectory(prefix="kw-kr7h10-check-dry-run-") as tmp:
            output_dir = Path(tmp) / "bundle"
            code, result, diagnostics = _run_json([
                "node",
                script.name,
                "--json",
                "--stdin",
                "--output-dir",
                str(output_dir),
            ], cwd=worker_root, stdin_payload=_source_backed_dry_run_payload())
            if code != 0 or not isinstance(result, dict):
                problems.append(f"source-backed dry-run artifact bundle smoke did not return ready JSON: {diagnostics}")
            else:
                _validate_result(result, output_dir, problems, label="source_backed_dry_run")
    status = "ready" if not problems else "blocked"
    return {"schema_version": "kw_renderer_worker_pptx_artifact_bundle_check.v1", "status": status, "problems": problems}


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
        print(f"kw_renderer_worker_pptx_artifact_bundle_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
