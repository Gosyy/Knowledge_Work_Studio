#!/usr/bin/env python3
"""KR-7H.11 renderer worker LibreOffice proof bundle contract checker."""
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

SCHEMA_VERSION = "presentation_renderer_worker_libreoffice_proof_bundle.v1"
ARTIFACT_SCHEMA_VERSION = "presentation_renderer_worker_pptx_artifact_bundle.v1"
RENDER_REPORT_SCHEMA_VERSION = "presentation_renderer_worker_render_report.v1"
EXPECTED_PPTXGENJS_VERSION = "4.0.1"
INTERNAL_REGISTRY_MARKERS = ("packages.applied-caas", "internal.api.openai.org")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _node_available() -> bool:
    return shutil.which("node") is not None


def _npm_available() -> bool:
    return shutil.which("npm") is not None


def _libreoffice_available() -> bool:
    return bool(shutil.which("soffice") or shutil.which("libreoffice"))


def _pdftoppm_available() -> bool:
    return shutil.which("pdftoppm") is not None


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
        timeout=240,
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
        problems.append("npm executable is required for KR-7H.11 LibreOffice proof bundle check")
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
        source_id="src_renderer_kr7h11_check",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    planner_result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h11_check",
            title="Support automation results",
            objective="Support automation retention risk",
            slide_count=4,
            required_sections=("retention", "risk"),
            require_evidence=True,
        ),
        index,
    )
    if planner_result.presentation_ir is None:
        raise AssertionError("planner_result.presentation_ir is required for KR-7H.11 source-backed smoke")
    dry_run = build_renderer_worker_dry_run_report(planner_result.presentation_ir, request_id="req_kr7h11_check")
    if dry_run.status != "ready":
        raise AssertionError(f"dry-run status must be ready, got {dry_run.status!r}")
    return dry_run.as_dict()


def _load_json(path: Path, problems: list[str], label: str) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - checker must report diagnostics, not crash.
        problems.append(f"{label}: invalid JSON at {path}: {exc}")
        return None


def _validate_output_files(result: dict[str, Any], output_dir: Path, problems: list[str], label: str) -> None:
    expected_files = {
        "pptx_artifact_basename": ".pptx",
        "render_report_basename": ".json",
        "pdf_proof_basename": ".pdf",
        "proof_bundle_basename": ".json",
    }
    for key, suffix in expected_files.items():
        basename = result.get(key)
        if not isinstance(basename, str) or not basename.endswith(suffix):
            problems.append(f"{label}: {key} must be a {suffix} basename string")
            return
        path = output_dir / basename
        if not path.is_file() or path.stat().st_size <= 0:
            problems.append(f"{label}: expected non-empty file for {key}: {path}")
    proof_dir_name = result.get("png_proof_directory")
    if proof_dir_name != "kr7h11-png-proof":
        problems.append(f"{label}: png_proof_directory expected 'kr7h11-png-proof', got {proof_dir_name!r}")
        return
    proof_dir = output_dir / proof_dir_name
    basenames = result.get("png_proof_basenames")
    sizes = result.get("png_proof_size_bytes")
    if not isinstance(basenames, list) or not basenames:
        problems.append(f"{label}: png_proof_basenames must contain at least one PNG")
        return
    if not isinstance(sizes, list) or len(sizes) != len(basenames):
        problems.append(f"{label}: png_proof_size_bytes must align with png_proof_basenames")
        return
    for basename, size in zip(basenames, sizes, strict=True):
        if not isinstance(basename, str) or not basename.endswith(".png"):
            problems.append(f"{label}: PNG proof basename is invalid: {basename!r}")
            continue
        path = proof_dir / basename
        if not path.is_file() or path.stat().st_size <= 0:
            problems.append(f"{label}: PNG proof is missing or empty: {path}")
        if not isinstance(size, int) or size <= 0:
            problems.append(f"{label}: PNG proof size must be > 0 for {basename!r}")
    proof_json = _load_json(output_dir / result["proof_bundle_basename"], problems, label)
    if proof_json is None:
        return
    if proof_json.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"{label}: proof bundle JSON schema_version mismatch: {proof_json.get('schema_version')!r}")
    if proof_json.get("status") != "ready":
        problems.append(f"{label}: proof bundle JSON status must be ready")
    if proof_json.get("fake_proof_used") is not False or proof_json.get("fallback_renderer_used") is not False:
        problems.append(f"{label}: proof bundle JSON must explicitly reject fake/fallback proof")


def _validate_result(result: dict[str, Any], output_dir: Path, problems: list[str], label: str) -> None:
    expected_values = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "artifact_bundle_schema_version": ARTIFACT_SCHEMA_VERSION,
        "render_report_schema_version": RENDER_REPORT_SCHEMA_VERSION,
        "proof_bundle_schema_version": SCHEMA_VERSION,
        "artifact_bundle_produced": True,
        "artifact_bundle_verified": True,
        "upstream_artifact_bundle_status": "ready",
        "pptx_artifact_exists": True,
        "render_report_exists": True,
        "proof_bundle_written": True,
        "proof_bundle_exists": True,
        "proof_bundle_file_size_nonzero": True,
        "proof_bundle_produced": True,
        "proof_bundle_verified": True,
        "proof_bundle_deterministic": True,
        "libreoffice_required": True,
        "pdftoppm_required": True,
        "libreoffice_available": True,
        "pdftoppm_available": True,
        "libreoffice_executed": True,
        "pdftoppm_executed": True,
        "pdf_proof_written": True,
        "pdf_proof_exists": True,
        "pdf_proof_file_size_nonzero": True,
        "png_proofs_written": True,
        "title_body_mapping_implemented": True,
        "presentation_ir_mapping_implemented": True,
        "chart_mapping_implemented": False,
        "table_mapping_implemented": False,
        "image_mapping_implemented": False,
        "theme_mapping_implemented": False,
        "professional_layout_engine_implemented": False,
        "production_pptx_output_implemented": False,
        "renderer_runtime_implemented": False,
        "visual_qa_executed": False,
        "fake_proof_used": False,
        "fallback_renderer_used": False,
        "python_pptx_proof_used": False,
        "output_mode": "persistent_pptx_artifact_bundle_plus_libreoffice_pdftoppm_proof_smoke_only",
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
    for key in ("pptx_artifact_size_bytes", "render_report_size_bytes", "pdf_proof_size_bytes", "proof_bundle_size_bytes", "png_proof_count"):
        if not isinstance(result.get(key), int) or result[key] <= 0:
            problems.append(f"{label}: {key} must be an integer > 0")
    for key in ("pptx_artifact_sha256", "pdf_proof_sha256"):
        if not isinstance(result.get(key), str) or not result[key].startswith("sha256:"):
            problems.append(f"{label}: {key} must be a sha256 digest")
    if result.get("visual_quality_score") is not None:
        problems.append(f"{label}: visual_quality_score must stay null in KR-7H.11")
    if result.get("issues") != []:
        problems.append(f"{label}: issues must be empty, got {result.get('issues')!r}")
    _validate_output_files(result, output_dir, problems, label)


def _validate_missing_tool_fail_closed(worker_root: Path, problems: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="kw-kr7h11-check-missing-tool-") as tmp:
        output_dir = Path(tmp) / "bundle"
        missing = Path(tmp) / "missing-soffice"
        code, result, diagnostics = _run_json(
            [
                "node",
                "kw_renderer_worker_libreoffice_proof_bundle_smoke.mjs",
                "--json",
                "--fixture",
                "--output-dir",
                str(output_dir),
                "--soffice-bin",
                str(missing),
            ],
            cwd=worker_root,
        )
        if code == 0 or not isinstance(result, dict):
            problems.append(f"missing LibreOffice fail-closed smoke should return non-zero JSON: {diagnostics}")
            return
        if result.get("status") != "blocked":
            problems.append(f"missing LibreOffice fail-closed status expected blocked, got {result.get('status')!r}")
        if result.get("proof_bundle_produced") is not False or result.get("libreoffice_executed") is not False:
            problems.append("missing LibreOffice fail-closed path must not produce proof or execute LibreOffice")
        issue_codes = {item.get("code") for item in result.get("issues", []) if isinstance(item, dict)}
        if "libreoffice_unavailable" not in issue_codes:
            problems.append(f"missing LibreOffice fail-closed issues must include libreoffice_unavailable, got {issue_codes!r}")


def check(repo_root: Path) -> dict[str, Any]:
    problems: list[str] = []
    worker_root = repo_root / "renderer_worker"
    script = worker_root / "kw_renderer_worker_libreoffice_proof_bundle_smoke.mjs"
    required_files = [
        script,
        worker_root / "kw_renderer_worker_pptx_artifact_bundle_smoke.mjs",
        repo_root / "scripts" / "kw_renderer_worker_libreoffice_proof_bundle_check.py",
        repo_root / "backend" / "tests" / "services" / "test_kr7h_renderer_worker_libreoffice_proof_bundle.py",
        worker_root / "package.json",
        worker_root / "package-lock.json",
        worker_root / "CONTRACT.md",
    ]
    for file in required_files:
        if not file.is_file():
            problems.append(f"required file is missing: {file.relative_to(repo_root)}")
    if problems:
        return {"schema_version": "kw_renderer_worker_libreoffice_proof_bundle_check.v1", "status": "blocked", "problems": problems}
    if not _node_available():
        problems.append("node executable is required for KR-7H.11 LibreOffice proof bundle check")
    if not _libreoffice_available():
        problems.append("LibreOffice/soffice executable is required for KR-7H.11 proof bundle check")
    if not _pdftoppm_available():
        problems.append("pdftoppm executable is required for KR-7H.11 proof bundle check")
    _validate_lockfile(repo_root, problems)
    syntax = subprocess.run(["node", "--check", script.name], cwd=worker_root, text=True, capture_output=True, check=False)
    if syntax.returncode != 0:
        problems.append(f"node --check renderer_worker/{script.name} failed: {syntax.stdout}{syntax.stderr}")
    if not problems:
        _ensure_npm_install(worker_root, problems)
    if not problems:
        with tempfile.TemporaryDirectory(prefix="kw-kr7h11-check-fixture-") as tmp:
            output_dir = Path(tmp) / "bundle"
            code, result, diagnostics = _run_json(
                [
                    "node",
                    script.name,
                    "--json",
                    "--fixture",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=worker_root,
            )
            if code != 0 or not isinstance(result, dict):
                problems.append(f"fixture LibreOffice proof bundle smoke did not return ready JSON: {diagnostics}")
            else:
                _validate_result(result, output_dir, problems, label="fixture")
    if not problems:
        with tempfile.TemporaryDirectory(prefix="kw-kr7h11-check-dry-run-") as tmp:
            output_dir = Path(tmp) / "bundle"
            code, result, diagnostics = _run_json(
                [
                    "node",
                    script.name,
                    "--json",
                    "--stdin",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=worker_root,
                stdin_payload=_source_backed_dry_run_payload(),
            )
            if code != 0 or not isinstance(result, dict):
                problems.append(f"source-backed dry-run LibreOffice proof bundle smoke did not return ready JSON: {diagnostics}")
            else:
                _validate_result(result, output_dir, problems, label="source-backed")
                if result.get("input_schema_version") != "presentation_renderer_worker_dry_run.v1":
                    problems.append("source-backed: input_schema_version must record dry-run schema")
    if not problems:
        _validate_missing_tool_fail_closed(worker_root, problems)
    return {
        "schema_version": "kw_renderer_worker_libreoffice_proof_bundle_check.v1",
        "status": "ready" if not problems else "blocked",
        "phase": "KR-7H.11 LibreOffice proof bundle smoke",
        "proof_bundle_schema_version": SCHEMA_VERSION,
        "artifact_bundle_schema_version": ARTIFACT_SCHEMA_VERSION,
        "render_report_schema_version": RENDER_REPORT_SCHEMA_VERSION,
        "expected_pptxgenjs_version": EXPECTED_PPTXGENJS_VERSION,
        "libreoffice_available": _libreoffice_available(),
        "pdftoppm_available": _pdftoppm_available(),
        "checked_files": [str(file.relative_to(repo_root)) for file in required_files],
        "problems": problems,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    result = check(repo_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
