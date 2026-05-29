#!/usr/bin/env python3
"""KR-7H.6 PptxGenJS in-memory construction preflight checker.

This checker verifies the first controlled PptxGenJS API-level smoke inside the
isolated renderer_worker package. It may construct a presentation object in
memory only. It must not write PPTX files, map PresentationIR blocks into
slides, run LibreOffice, write artifact/proof bundles, or claim production
renderer readiness.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1"
EXPECTED_VERSION = "4.0.1"

REQUIRED_FILES = [
    "renderer_worker/package.json",
    "renderer_worker/package-lock.json",
    "renderer_worker/CONTRACT.md",
    "renderer_worker/kw_renderer_worker_pptxgenjs_in_memory_preflight.mjs",
    "backend/tests/services/test_kr7h_renderer_worker_pptxgenjs_in_memory.py",
    "scripts/kw_renderer_worker_pptxgenjs_in_memory_check.py",
]

REQUIRED_PHRASES = {
    "renderer_worker/package.json": [
        '"pptxgenjs:in-memory"',
        '"presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1"',
        '"pptxgenjs_in_memory_preflight_implemented": true',
        '"pptxgenjs_in_memory_object_created": true',
        '"slide_content_added": false',
        '"pptxgenjs_write_api_called": false',
        '"filesystem_output_written": false',
        '"renderer_runtime_implemented": false',
        '"production_pptx_output_implemented": false',
        '"pptx_generation_executed": false',
        '"artifact_bundle_produced": false',
        '"proof_bundle_produced": false',
        '"no_slide_content_generation"',
    ],
    "renderer_worker/CONTRACT.md": [
        "KR-7H.6 extends that boundary with an in-memory PptxGenJS construction preflight",
        "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1",
        "npm run pptxgenjs:in-memory --prefix renderer_worker",
        "slide_content_added=false",
        "pptxgenjs_write_api_called=false",
        "filesystem_output_written=false",
        "does not write .pptx files",
        "does not map PresentationIR blocks into slides",
    ],
    "renderer_worker/kw_renderer_worker_pptxgenjs_in_memory_preflight.mjs": [
        "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1",
        "new PptxGenJS()",
        "in_memory_construction_preflight_only",
        "write_api_called: false",
        "filesystem_output_written: false",
        "no_pptx_generation",
        "no_pptxgenjs_write_or_output_calls",
    ],
    "backend/tests/services/test_kr7h_renderer_worker_pptxgenjs_in_memory.py": [
        "test_kr7h6_in_memory_preflight_constructs_object_without_output",
        "test_kr7h6_in_memory_preflight_contract_blocks_write_and_artifact_claims",
        "test_kr7h6_package_check_runs_in_memory_script_without_frontend_changes",
    ],
    "scripts/kw_full_tests_with_proxy_runner.sh": [
        "29h6-renderer-worker-pptxgenjs-in-memory-check",
        "kw_renderer_worker_pptxgenjs_in_memory_check.py --repo-root . --require-ready",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7H.6 in-memory PptxGenJS construction preflight",
        "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1",
        "does not write .pptx files",
        "does not map PresentationIR blocks into slides",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "KR-7H.6 in-memory PptxGenJS construction preflight",
        "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1",
        "no PPTX file output",
        "no PresentationIR mapping",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7H.6 in-memory PptxGenJS construction preflight",
        "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1",
        "does not write .pptx files",
        "does not produce artifact/proof bundles",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7H.6 adds in-memory PptxGenJS construction preflight",
        "without PPTX file output, PresentationIR mapping, or LibreOffice proof runtime",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim KR-7H.6 writes PPTX files",
        "claim KR-7H.6 maps PresentationIR blocks into slides",
        "claim KR-7H.6 produces artifact/proof bundles",
    ],
}

FORBIDDEN_TEXT = {
    "renderer_worker/kw_renderer_worker_pptxgenjs_in_memory_preflight.mjs": [
        ".writeFile(",
        ".write(",
        ".stream(",
        ".output(",
        ".addSlide(",
        "fs.writeFile",
    ],
}


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


def _validate_package(repo_root: Path, problems: list[str]) -> None:
    package = _load_json(repo_root / "renderer_worker" / "package.json")
    dependencies = package.get("dependencies")
    if not isinstance(dependencies, dict) or dependencies.get("pptxgenjs") != EXPECTED_VERSION:
        problems.append("renderer_worker/package.json must declare pptxgenjs@4.0.1")
    elif set(dependencies) != {"pptxgenjs"}:
        problems.append(f"renderer_worker dependencies must contain only pptxgenjs, got {sorted(dependencies)}")
    metadata = package.get("kwStudio") if isinstance(package.get("kwStudio"), dict) else {}
    expected = {
        "pptxgenjs_in_memory_schema_version": SCHEMA_VERSION,
        "pptxgenjs_in_memory_preflight_implemented": True,
        "pptxgenjs_in_memory_object_created": True,
        "slide_content_added": False,
        "pptxgenjs_write_api_called": False,
        "filesystem_output_written": False,
        "renderer_runtime_implemented": False,
        "production_pptx_output_implemented": False,
        "pptx_generation_executed": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
    }
    for key, expected_value in expected.items():
        if metadata.get(key) != expected_value:
            problems.append(f"kwStudio.{key} expected {expected_value!r}, got {metadata.get(key)!r}")
    scripts = package.get("scripts") if isinstance(package.get("scripts"), dict) else {}
    if "kw_renderer_worker_pptxgenjs_in_memory_preflight.mjs" not in str(scripts.get("pptxgenjs:in-memory", "")):
        problems.append("renderer_worker/package.json must define pptxgenjs:in-memory script")
    if "pptxgenjs:in-memory" not in str(scripts.get("check", "")):
        problems.append("renderer_worker/package.json check script must run pptxgenjs:in-memory")


def _run_in_memory(repo_root: Path, problems: list[str]) -> None:
    if not _node_available():
        problems.append("node executable is required for KR-7H.6 in-memory check")
        return
    if not _npm_available():
        problems.append("npm executable is required for KR-7H.6 in-memory check")
        return
    worker_root = repo_root / "renderer_worker"
    _ensure_npm_install(worker_root, problems)
    if problems:
        return

    syntax = subprocess.run(
        ["node", "--check", "kw_renderer_worker_pptxgenjs_in_memory_preflight.mjs"],
        cwd=worker_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if syntax.returncode != 0:
        problems.append(f"node --check kw_renderer_worker_pptxgenjs_in_memory_preflight.mjs failed: {syntax.stdout}{syntax.stderr}")
        return

    code, payload, diagnostics = _run_json(["npm", "run", "pptxgenjs:in-memory", "--silent"], cwd=worker_root)
    if code != 0 or not isinstance(payload, dict):
        problems.append(f"npm run pptxgenjs:in-memory --prefix renderer_worker failed: {diagnostics}")
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
        "in_memory_preflight_implemented": True,
        "presentation_object_created": True,
        "presentation_object_type": "PptxGenJS",
        "slide_count": 0,
        "slide_content_added": False,
        "write_api_called": False,
        "filesystem_output_written": False,
        "renderer_runtime_implemented": False,
        "production_pptx_output_implemented": False,
        "pptx_generation_executed": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
        "output_mode": "in_memory_construction_preflight_only",
    }
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value:
            problems.append(f"in-memory {key} expected {expected_value!r}, got {payload.get(key)!r}")
    if payload.get("issues") != []:
        problems.append(f"in-memory issues expected [], got {payload.get('issues')!r}")
    blocked = payload.get("blocked_runtime_actions") if isinstance(payload.get("blocked_runtime_actions"), list) else []
    for action in ("call_pptxgenjs_write_or_output_api", "write_pptx_file", "map_presentation_ir_to_slides", "write_artifact_bundle"):
        if action not in blocked:
            problems.append(f"in-memory blocked_runtime_actions missing {action}")


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
            _validate_package(repo_root, problems)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"package validation failed: {exc}")
        if not problems:
            _run_in_memory(repo_root, problems)

    status = "ready" if not missing_files and not missing_phrases and not forbidden_hits and not problems else "blocked"
    return {
        "schema_version": "kw_renderer_worker_pptxgenjs_in_memory_check.v1",
        "status": status,
        "missing_files": missing_files,
        "missing_phrases": missing_phrases,
        "forbidden_hits": forbidden_hits,
        "in_memory_problems": problems,
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
        print(f"kw_renderer_worker_pptxgenjs_in_memory_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
