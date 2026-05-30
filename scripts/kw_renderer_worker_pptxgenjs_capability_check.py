#!/usr/bin/env python3
"""Validate KR-7H.5 controlled PptxGenJS capability preflight."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

CAPABILITY_SCHEMA_VERSION = "presentation_renderer_worker_pptxgenjs_capability.v1"
EXPECTED_VERSION = "4.0.1"

REQUIRED_FILES = [
    "renderer_worker/package.json",
    "renderer_worker/package-lock.json",
    "renderer_worker/kw_renderer_worker_pptxgenjs_capability.mjs",
    "backend/tests/services/test_kr7h_renderer_worker_pptxgenjs_capability.py",
    "scripts/kw_renderer_worker_pptxgenjs_capability_check.py",
]

REQUIRED_PHRASES = {
    "renderer_worker/kw_renderer_worker_pptxgenjs_capability.mjs": [
        'CAPABILITY_SCHEMA_VERSION = "presentation_renderer_worker_pptxgenjs_capability.v1"',
        'EXPECTED_PACKAGE_NAME = "pptxgenjs"',
        'EXPECTED_PACKAGE_VERSION = "4.0.1"',
        "dependency_capability_preflight_only",
        "pptx_generation_executed: false",
        "renderer_runtime_implemented: false",
        "production_pptx_output_implemented: false",
        "artifact_bundle_produced: false",
        "proof_bundle_produced: false",
        "no_pptx_generation",
        "no_libreoffice_execution",
        "write_pptx_file",
    ],
    "renderer_worker/package.json": [
        '"pptxgenjs": "4.0.1"',
        '"dependency:capability"',
        '"presentation_renderer_worker_pptxgenjs_capability.v1"',
        '"pptxgenjs_dependency_declared": true',
        '"pptx_generation_executed": false',
    ],
    "renderer_worker/package-lock.json": [
        '"node_modules/pptxgenjs"',
        '"version": "4.0.1"',
    ],
    "backend/tests/services/test_kr7h_renderer_worker_pptxgenjs_capability.py": [
        "test_kr7h5_capability_script_reports_pinned_pptxgenjs_without_generation",
        "test_kr7h5_package_keeps_dependency_isolated_from_frontend",
        "test_kr7h5_capability_contract_blocks_runtime_and_artifact_claims",
    ],
    "scripts/kw_full_tests_with_proxy_runner.sh": [
        "29h5-renderer-worker-pptxgenjs-capability-check",
        "kw_renderer_worker_pptxgenjs_capability_check.py --repo-root . --require-ready",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7H.5 controlled PptxGenJS capability preflight",
        "presentation_renderer_worker_pptxgenjs_capability.v1",
        "does not generate PPTX",
        "does not run LibreOffice",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "KR-7H.5 controlled PptxGenJS capability preflight",
        "PptxGenJS dependency is introduced only inside renderer_worker",
        "no production PPTX",
        "no LibreOffice proof",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7H.5 controlled PptxGenJS capability preflight",
        "PptxGenJS dependency is introduced only inside renderer_worker",
        "does not generate PPTX",
        "does not run LibreOffice",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7H.5 adds controlled PptxGenJS capability preflight",
        "without PPTX generation or LibreOffice proof runtime",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim KR-7H.5 generates PPTX",
        "claim KR-7H.5 maps PresentationIR blocks into slides",
        "claim KR-7H.5 dependency capability preflight responses are rendered deck artifacts",
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
    for forbidden in ("devDependencies", "optionalDependencies", "peerDependencies"):
        if forbidden in package:
            problems.append(f"renderer_worker/package.json must not declare {forbidden} in KR-7H.5")
    metadata = package.get("kwStudio") if isinstance(package.get("kwStudio"), dict) else {}
    expected = {
        "pptxgenjs_capability_schema_version": CAPABILITY_SCHEMA_VERSION,
        "pptxgenjs_dependency_declared": True,
        "pptxgenjs_dependency_version": EXPECTED_VERSION,
        "pptxgenjs_capability_preflight_implemented": True,
        "renderer_runtime_implemented": False,
        "production_pptx_output_implemented": False,
        "pptx_generation_executed": False,
        # renderer_worker/package.json is cumulative package metadata. After KR-7H.11
        # the package advertises a real LibreOffice proof-bundle smoke while this
        # KR-7H.5 capability script still returns proof_bundle_produced=false.
        "proof_bundle_produced": True,
    }
    for key, expected_value in expected.items():
        if metadata.get(key) != expected_value:
            problems.append(f"kwStudio.{key} expected {expected_value!r}, got {metadata.get(key)!r}")

    frontend_text = _read(repo_root / "frontend" / "package.json").lower()
    if "pptxgenjs" in frontend_text or "kw-studio-renderer-worker" in frontend_text:
        problems.append("frontend/package.json must not contain renderer worker dependency markers in KR-7H.5")


def _run_capability(repo_root: Path, problems: list[str]) -> None:
    if not _node_available():
        problems.append("node executable is required for KR-7H.5 capability check")
        return
    if not _npm_available():
        problems.append("npm executable is required for KR-7H.5 capability check")
        return
    worker_root = repo_root / "renderer_worker"
    _ensure_npm_install(worker_root, problems)
    if problems:
        return

    syntax = subprocess.run(
        ["node", "--check", "kw_renderer_worker_pptxgenjs_capability.mjs"],
        cwd=worker_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if syntax.returncode != 0:
        problems.append(f"node --check kw_renderer_worker_pptxgenjs_capability.mjs failed: {syntax.stdout}{syntax.stderr}")
        return

    code, payload, diagnostics = _run_json(["npm", "run", "dependency:capability", "--silent"], cwd=worker_root)
    if code != 0 or not isinstance(payload, dict):
        problems.append(f"npm run dependency:capability --prefix renderer_worker failed: {diagnostics}")
        return
    expected = {
        "schema_version": CAPABILITY_SCHEMA_VERSION,
        "status": "ready",
        "dependency_name": "pptxgenjs",
        "expected_dependency_version": EXPECTED_VERSION,
        "dependency_available": True,
        "dependency_version": EXPECTED_VERSION,
        "module_default_export_type": "function",
        "renderer_runtime_implemented": False,
        "production_pptx_output_implemented": False,
        "pptx_generation_executed": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
        "output_mode": "dependency_capability_preflight_only",
    }
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value:
            problems.append(f"capability {key} expected {expected_value!r}, got {payload.get(key)!r}")
    if payload.get("issues") != []:
        problems.append(f"capability issues expected [], got {payload.get('issues')!r}")
    blocked = payload.get("blocked_runtime_actions") if isinstance(payload.get("blocked_runtime_actions"), list) else []
    for action in ("generate_editable_pptx", "write_pptx_file", "run_libreoffice_pdf_export", "write_artifact_bundle"):
        if action not in blocked:
            problems.append(f"capability blocked_runtime_actions missing {action}")


def check(repo_root: Path) -> dict[str, Any]:
    missing_files = [path for path in REQUIRED_FILES if not (repo_root / path).is_file()]
    missing_phrases: dict[str, list[str]] = {}
    for relative_path, phrases in REQUIRED_PHRASES.items():
        path = repo_root / relative_path
        if not path.is_file():
            missing_phrases[relative_path] = phrases
            continue
        text = _read(path)
        absent = [phrase for phrase in phrases if phrase not in text]
        if absent:
            missing_phrases[relative_path] = absent

    capability_problems: list[str] = []
    if not missing_files and not missing_phrases:
        try:
            _validate_package(repo_root, capability_problems)
        except Exception as exc:  # noqa: BLE001
            capability_problems.append(f"package validation failed: {exc}")
        if not capability_problems:
            _run_capability(repo_root, capability_problems)

    status = "ready" if not missing_files and not missing_phrases and not capability_problems else "blocked"
    return {
        "schema_version": "kw_renderer_worker_pptxgenjs_capability_check.v1",
        "status": status,
        "missing_files": missing_files,
        "missing_phrases": missing_phrases,
        "capability_problems": capability_problems,
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
        print(f"kw_renderer_worker_pptxgenjs_capability_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
