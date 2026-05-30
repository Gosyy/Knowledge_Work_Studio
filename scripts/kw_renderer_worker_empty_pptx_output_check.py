#!/usr/bin/env python3
"""KR-7H.7 controlled empty PPTX output smoke checker.

This checker verifies that the isolated renderer_worker package can perform a
controlled temporary PptxGenJS file-output smoke. It may write an empty .pptx
file only in a temporary directory and must delete that file before returning
ready. It must not persist artifacts, map PresentationIR blocks into slides, run
LibreOffice, write proof bundles, or claim production renderer readiness.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "presentation_renderer_worker_empty_pptx_output_smoke.v1"
EXPECTED_VERSION = "4.0.1"

REQUIRED_FILES = [
    "renderer_worker/package.json",
    "renderer_worker/package-lock.json",
    "renderer_worker/CONTRACT.md",
    "renderer_worker/kw_renderer_worker_empty_pptx_output_smoke.mjs",
    "backend/tests/services/test_kr7h_renderer_worker_empty_pptx_output.py",
    "scripts/kw_renderer_worker_empty_pptx_output_check.py",
]

REQUIRED_PHRASES = {
    "renderer_worker/package.json": [
        '"pptxgenjs:empty-output"',
        '"presentation_renderer_worker_empty_pptx_output_smoke.v1"',
        '"empty_pptx_output_smoke_implemented": true',
        '"temporary_pptx_write_api_called": true',
        '"temporary_pptx_written": true',
        '"temporary_pptx_deleted": true',
        '"temporary_pptx_file_size_nonzero": true',
        '"persistent_artifact_written": false',
        '"filesystem_output_written": false',
        '"renderer_runtime_implemented": false',
        '"production_pptx_output_implemented": false',
        '"artifact_bundle_produced": false',
        '"proof_bundle_produced": false',
        '"libreoffice_executed": false',
        '"visual_qa_executed": false',
    ],
    "renderer_worker/CONTRACT.md": [
        "KR-7H.7 extends that boundary with a controlled empty PPTX file output smoke",
        "presentation_renderer_worker_empty_pptx_output_smoke.v1",
        "npm run pptxgenjs:empty-output --prefix renderer_worker",
        "temporary_pptx_written=true",
        "temporary_pptx_deleted=true",
        "persistent_artifact_written=false",
        "presentation_ir_mapping_implemented=false",
        "production_pptx_output_implemented=false",
    ],
    "renderer_worker/kw_renderer_worker_empty_pptx_output_smoke.mjs": [
        "presentation_renderer_worker_empty_pptx_output_smoke.v1",
        "writeFile({ fileName: outputPath })",
        "temporary_empty_pptx_output_smoke_only",
        "temporary_pptx_written",
        "temporary_pptx_deleted",
        "persistent_artifact_written: false",
        "filesystem_output_written: false",
        "libreoffice_executed: false",
        "visual_qa_executed: false",
    ],
    "backend/tests/services/test_kr7h_renderer_worker_empty_pptx_output.py": [
        "test_kr7h7_empty_output_smoke_writes_and_deletes_temporary_pptx",
        "test_kr7h7_empty_output_smoke_contract_blocks_persistent_artifacts",
        "test_kr7h7_package_check_runs_empty_output_without_frontend_changes",
    ],
    "scripts/kw_full_tests_with_proxy_runner.sh": [
        "29h7-renderer-worker-empty-pptx-output-check",
        "kw_renderer_worker_empty_pptx_output_check.py --repo-root . --require-ready",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7H.7 controlled empty PPTX file output smoke",
        "presentation_renderer_worker_empty_pptx_output_smoke.v1",
        "temporary_pptx_written=true",
        "temporary_pptx_deleted=true",
        "does not map PresentationIR blocks into slides",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "KR-7H.7 controlled empty PPTX file output smoke",
        "temporary empty `.pptx`",
        "no PresentationIR mapping",
        "no persistent artifact",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7H.7 controlled empty PPTX file output smoke",
        "presentation_renderer_worker_empty_pptx_output_smoke.v1",
        "temporary_pptx_written=true",
        "temporary_pptx_deleted=true",
        "does not produce artifact/proof bundles",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7H.7 adds controlled empty PPTX file output smoke",
        "temporary `.pptx`",
        "without PresentationIR mapping, persistent artifacts, or LibreOffice proof runtime",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim KR-7H.7 creates production PPTX output",
        "claim KR-7H.7 maps PresentationIR blocks into slides",
        "claim KR-7H.7 produces artifact/proof bundles",
    ],
}

FORBIDDEN_TEXT = {
    "renderer_worker/kw_renderer_worker_empty_pptx_output_smoke.mjs": [
        ".addSlide(",
        "runLibreOffice",
        "artifact_bundle_produced: true",
        "proof_bundle_produced: true",
        "persistent_artifact_written: true",
        "production_pptx_output_implemented: true",
    ],
}

INTERNAL_REGISTRY_MARKERS = ("packages.applied-caas", "internal.api.openai.org", "artifactory/api/npm")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _load_json(path: Path) -> Any:
    return json.loads(_read(path))


def _node_available() -> bool:
    return shutil.which("node") is not None


def _npm_available() -> bool:
    return shutil.which("npm") is not None


def _run_json(command: list[str], *, cwd: Path | None = None) -> tuple[int, dict[str, Any] | None, str]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = None
    diagnostics = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    return completed.returncode, payload, diagnostics


def _worker_dependency_tree_ready(worker_root: Path) -> bool:
    return (worker_root / "node_modules" / "pptxgenjs" / "package.json").is_file()


def _ensure_npm_install(worker_root: Path, problems: list[str]) -> None:
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
    lock = _load_json(lock_path)
    packages = lock.get("packages") if isinstance(lock, dict) else {}
    root = packages.get("") if isinstance(packages, dict) else {}
    dependency = packages.get("node_modules/pptxgenjs") if isinstance(packages, dict) else {}
    if not isinstance(root, dict) or root.get("dependencies", {}).get("pptxgenjs") != EXPECTED_VERSION:
        problems.append("renderer_worker/package-lock.json root dependency must pin pptxgenjs@4.0.1")
    if not isinstance(dependency, dict) or dependency.get("version") != EXPECTED_VERSION:
        problems.append("renderer_worker/package-lock.json must lock node_modules/pptxgenjs version 4.0.1")


def _validate_package(repo_root: Path, problems: list[str]) -> None:
    package = _load_json(repo_root / "renderer_worker" / "package.json")
    dependencies = package.get("dependencies")
    if not isinstance(dependencies, dict) or dependencies.get("pptxgenjs") != EXPECTED_VERSION:
        problems.append("renderer_worker/package.json must declare pptxgenjs@4.0.1")
    elif set(dependencies) != {"pptxgenjs"}:
        problems.append(f"renderer_worker dependencies must contain only pptxgenjs, got {sorted(dependencies)}")
    metadata = package.get("kwStudio") if isinstance(package.get("kwStudio"), dict) else {}
    expected = {
        "empty_pptx_output_smoke_schema_version": SCHEMA_VERSION,
        "empty_pptx_output_smoke_implemented": True,
        "temporary_pptx_write_api_called": True,
        "temporary_pptx_written": True,
        "temporary_pptx_deleted": True,
        "temporary_pptx_file_size_nonzero": True,
        "persistent_artifact_written": False,
        "filesystem_output_written": False,
        "renderer_runtime_implemented": False,
        "production_pptx_output_implemented": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
        "libreoffice_executed": False,
        "visual_qa_executed": False,
    }
    for key, expected_value in expected.items():
        if metadata.get(key) != expected_value:
            problems.append(f"kwStudio.{key} expected {expected_value!r}, got {metadata.get(key)!r}")
    scripts = package.get("scripts") if isinstance(package.get("scripts"), dict) else {}
    if "kw_renderer_worker_empty_pptx_output_smoke.mjs" not in str(scripts.get("pptxgenjs:empty-output", "")):
        problems.append("renderer_worker/package.json must define pptxgenjs:empty-output script")
    if "pptxgenjs:empty-output" not in str(scripts.get("check", "")):
        problems.append("renderer_worker/package.json check script must run pptxgenjs:empty-output")


def _run_empty_output(repo_root: Path, problems: list[str]) -> None:
    if not _node_available():
        problems.append("node executable is required for KR-7H.7 empty PPTX output check")
        return
    if not _npm_available():
        problems.append("npm executable is required for KR-7H.7 empty PPTX output check")
        return
    worker_root = repo_root / "renderer_worker"
    _ensure_npm_install(worker_root, problems)
    if problems:
        return

    syntax = subprocess.run(
        ["node", "--check", "kw_renderer_worker_empty_pptx_output_smoke.mjs"],
        cwd=worker_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if syntax.returncode != 0:
        problems.append(f"node --check kw_renderer_worker_empty_pptx_output_smoke.mjs failed: {syntax.stdout}{syntax.stderr}")
        return

    code, payload, diagnostics = _run_json(["npm", "run", "pptxgenjs:empty-output", "--silent"], cwd=worker_root)
    if code != 0 or not isinstance(payload, dict):
        problems.append(f"npm run pptxgenjs:empty-output --prefix renderer_worker failed: {diagnostics}")
        return
    expected = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "dependency_name": "pptxgenjs",
        "expected_dependency_version": EXPECTED_VERSION,
        "dependency_available": True,
        "dependency_version": EXPECTED_VERSION,
        "module_default_export_type": "function",
        "module_default_export_name": "PptxGenJS",
        "empty_pptx_output_smoke_implemented": True,
        "temporary_pptx_write_api_called": True,
        "temporary_pptx_written": True,
        "temporary_pptx_deleted": True,
        "temporary_directory_removed": True,
        "temporary_output_basename": "kr7h7-empty-output-smoke.pptx",
        "temporary_pptx_file_size_nonzero": True,
        "slide_count": 0,
        "slide_content_added": False,
        "presentation_ir_mapping_implemented": False,
        "production_pptx_output_implemented": False,
        "renderer_runtime_implemented": False,
        "persistent_artifact_written": False,
        "filesystem_output_written": False,
        "pptx_generation_executed": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
        "libreoffice_executed": False,
        "visual_qa_executed": False,
        "output_mode": "temporary_empty_pptx_output_smoke_only",
    }
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value:
            problems.append(f"empty-output {key} expected {expected_value!r}, got {payload.get(key)!r}")
    size = payload.get("temporary_pptx_file_size_bytes")
    if not isinstance(size, int) or size <= 0:
        problems.append(f"empty-output temporary_pptx_file_size_bytes must be positive, got {size!r}")
    if payload.get("issues") != []:
        problems.append(f"empty-output issues expected [], got {payload.get('issues')!r}")
    blocked = payload.get("blocked_runtime_actions") if isinstance(payload.get("blocked_runtime_actions"), list) else []
    for action in ("map_presentation_ir_to_slides", "persist_pptx_artifact", "run_libreoffice_pdf_export", "write_artifact_bundle"):
        if action not in blocked:
            problems.append(f"empty-output blocked_runtime_actions missing {action}")


def check(repo_root: Path) -> dict[str, Any]:
    missing_files = [path for path in REQUIRED_FILES if not (repo_root / path).is_file()]
    missing_phrases: dict[str, list[str]] = {}
    forbidden_hits: dict[str, list[str]] = {}
    for relative_path, phrases in REQUIRED_PHRASES.items():
        path = repo_root / relative_path
        if not path.is_file():
            missing_phrases[relative_path] = phrases
            continue
        text = _read(path)
        absent = [phrase for phrase in phrases if phrase not in text]
        if absent:
            missing_phrases[relative_path] = absent
    for relative_path, phrases in FORBIDDEN_TEXT.items():
        path = repo_root / relative_path
        if path.is_file():
            text = _read(path)
            hits = [phrase for phrase in phrases if phrase in text]
            if hits:
                forbidden_hits[relative_path] = hits

    problems: list[str] = []
    if not missing_files and not missing_phrases and not forbidden_hits:
        try:
            _validate_lockfile(repo_root, problems)
            _validate_package(repo_root, problems)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"package validation failed: {exc}")
        if not problems:
            _run_empty_output(repo_root, problems)

    status = "ready" if not missing_files and not missing_phrases and not forbidden_hits and not problems else "blocked"
    return {
        "schema_version": "kw_renderer_worker_empty_pptx_output_check.v1",
        "status": status,
        "missing_files": missing_files,
        "missing_phrases": missing_phrases,
        "forbidden_hits": forbidden_hits,
        "empty_output_problems": problems,
    }


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
        print(f"kw_renderer_worker_empty_pptx_output_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
