#!/usr/bin/env python3
"""KR-7H.4 renderer worker package preflight contract checker.

This checker verifies that the renderer worker has an isolated package boundary
for future Node/PptxGenJS work without claiming renderer runtime readiness. It
runs deterministic package scripts, but it must not generate PPTX, import
PptxGenJS, run LibreOffice, write artifact/proof bundles, or touch frontend
runtime dependencies.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

PACKAGE_SCHEMA_VERSION = "presentation_renderer_worker_package_preflight.v1"
PROTOCOL_SCHEMA_VERSION = "presentation_renderer_worker_protocol_preflight.v1"
RESPONSE_SCHEMA_VERSION = "presentation_renderer_worker_protocol_preflight_response.v1"

REQUIRED_FILES = [
    "renderer_worker/package.json",
    "renderer_worker/CONTRACT.md",
    "renderer_worker/kw_renderer_worker_protocol_preflight.mjs",
    "backend/tests/services/test_kr7h_renderer_worker_package.py",
    "scripts/kw_renderer_worker_package_check.py",
]

REQUIRED_PHRASES = {
    "renderer_worker/package.json": [
        '"name": "kw-studio-renderer-worker"',
        '"private": true',
        '"type": "module"',
        '"protocol:preflight"',
        '"check"',
        '"presentation_renderer_worker_package_preflight.v1"',
        '"renderer_worker_package_boundary": true',
        '"frontend_package_boundary": false',
        '"renderer_runtime_implemented": false',
        '"production_pptx_output_implemented": false',
        '"artifact_bundle_produced": false',
        '"proof_bundle_produced": false',
        '"no_pptxgenjs_dependency"',
        '"no_frontend_package_changes"',
    ],
    "renderer_worker/CONTRACT.md": [
        "KR-7H.4 renderer worker package preflight contract",
        "presentation_renderer_worker_package_preflight.v1",
        "npm run protocol:preflight --prefix renderer_worker",
        "npm run check --prefix renderer_worker",
        "renderer_runtime_implemented=false",
        "production_pptx_output_implemented=false",
        "artifact_bundle_produced=false",
        "proof_bundle_produced=false",
        "does not add a PptxGenJS dependency",
        "does not generate production PPTX",
        "does not run LibreOffice",
        "does not change UI",
    ],
    "backend/tests/services/test_kr7h_renderer_worker_package.py": [
        "test_kr7h4_package_json_declares_isolated_renderer_worker_boundary",
        "test_kr7h4_package_scripts_run_protocol_preflight_without_runtime_output",
        "test_kr7h4_package_contract_blocks_renderer_runtime_claims",
        "test_kr7h4_frontend_package_is_not_used_for_renderer_worker_boundary",
    ],
    "scripts/kw_full_tests_with_proxy_runner.sh": [
        "29h4-renderer-worker-package-check",
        "kw_renderer_worker_package_check.py --repo-root . --require-ready",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7H.4 isolated renderer worker package preflight",
        "presentation_renderer_worker_package_preflight.v1",
        "does not add PptxGenJS dependency",
        "does not generate PPTX",
        "does not run LibreOffice",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "KR-7H.4 isolated renderer worker package preflight",
        "renderer_worker package boundary",
        "presentation_renderer_worker_package_preflight.v1",
        "no PptxGenJS dependency",
        "no production PPTX",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7H.4 isolated renderer worker package preflight",
        "renderer_worker package boundary",
        "does not add PptxGenJS dependency",
        "does not generate PPTX",
        "does not run LibreOffice",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7H.4 adds isolated renderer worker package preflight",
        "without PptxGenJS dependency or PPTX runtime",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim KR-7H.4 generates PPTX",
        "claim KR-7H.4 adds or executes PptxGenJS",
        "claim KR-7H.4 package preflight responses are rendered deck artifacts",
    ],
}

FORBIDDEN_PACKAGE_FIELDS = ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")
FORBIDDEN_FRONTEND_PHRASES = ("pptxgenjs", "kw-studio-renderer-worker")


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


def _validate_package_json(repo_root: Path, problems: list[str]) -> None:
    path = repo_root / "renderer_worker" / "package.json"
    try:
        package = _load_json(path)
    except Exception as exc:  # noqa: BLE001 - checker reports concrete validation failures
        problems.append(f"renderer_worker/package.json is not valid JSON: {exc}")
        return

    if package.get("name") != "kw-studio-renderer-worker":
        problems.append("renderer_worker/package.json name must be kw-studio-renderer-worker")
    if package.get("private") is not True:
        problems.append("renderer_worker/package.json must be private")
    if package.get("type") != "module":
        problems.append("renderer_worker/package.json type must be module")

    scripts = package.get("scripts")
    if not isinstance(scripts, dict):
        problems.append("renderer_worker/package.json scripts must be an object")
    else:
        protocol_script = scripts.get("protocol:preflight")
        check_script = scripts.get("check")
        if not isinstance(protocol_script, str) or "kw_renderer_worker_protocol_preflight.mjs" not in protocol_script:
            problems.append("protocol:preflight script must call kw_renderer_worker_protocol_preflight.mjs")
        if not isinstance(check_script, str) or "node --check" not in check_script or "protocol:preflight" not in check_script:
            problems.append("check script must run node --check and protocol:preflight")

    for field in FORBIDDEN_PACKAGE_FIELDS:
        if field in package:
            problems.append(f"renderer_worker/package.json must not declare {field} in KR-7H.4")

    metadata = package.get("kwStudio")
    if not isinstance(metadata, dict):
        problems.append("renderer_worker/package.json kwStudio metadata must be an object")
        return
    expected = {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "renderer_worker_package_boundary": True,
        "frontend_package_boundary": False,
        "renderer_runtime_implemented": False,
        "production_pptx_output_implemented": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
    }
    for key, expected_value in expected.items():
        if metadata.get(key) != expected_value:
            problems.append(f"renderer_worker kwStudio.{key} expected {expected_value!r}, got {metadata.get(key)!r}")
    non_goals = metadata.get("non_goals") if isinstance(metadata.get("non_goals"), list) else []
    for non_goal in ("no_pptxgenjs_dependency", "no_pptx_generation", "no_libreoffice_execution", "no_frontend_package_changes"):
        if non_goal not in non_goals:
            problems.append(f"renderer_worker kwStudio.non_goals missing {non_goal}")


def _validate_frontend_package(repo_root: Path, problems: list[str]) -> None:
    frontend_package = repo_root / "frontend" / "package.json"
    if not frontend_package.is_file():
        return
    text = _read(frontend_package).lower()
    for phrase in FORBIDDEN_FRONTEND_PHRASES:
        if phrase in text:
            problems.append(f"frontend/package.json must not contain renderer worker dependency marker {phrase!r} in KR-7H.4")


def _run_package_scripts(repo_root: Path, problems: list[str]) -> None:
    if not _node_available():
        problems.append("node executable is required for KR-7H.4 package preflight check")
        return
    if not _npm_available():
        problems.append("npm executable is required for KR-7H.4 package preflight check")
        return

    worker_root = repo_root / "renderer_worker"
    syntax = subprocess.run(
        ["node", "--check", "kw_renderer_worker_protocol_preflight.mjs"],
        cwd=worker_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if syntax.returncode != 0:
        problems.append(f"renderer_worker protocol script syntax failed: {syntax.stdout}{syntax.stderr}")
        return

    check = subprocess.run(
        ["npm", "run", "check", "--silent"],
        cwd=worker_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if check.returncode != 0:
        problems.append(f"npm run check --prefix renderer_worker failed: {check.stdout}{check.stderr}")
        return

    code, capabilities, diagnostics = _run_json(["npm", "run", "protocol:preflight", "--silent"], cwd=worker_root)
    if code != 0 or not isinstance(capabilities, dict):
        problems.append(f"npm run protocol:preflight --prefix renderer_worker did not return JSON: {diagnostics}")
        return
    expected_caps = {
        "schema_version": PROTOCOL_SCHEMA_VERSION,
        "renderer_runtime_implemented": False,
        "production_pptx_output_implemented": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
    }
    for key, expected in expected_caps.items():
        if capabilities.get(key) != expected:
            problems.append(f"renderer_worker protocol capabilities {key} expected {expected!r}, got {capabilities.get(key)!r}")
    non_goals = capabilities.get("non_goals") if isinstance(capabilities.get("non_goals"), list) else []
    if "no_pptxgenjs_dependency" not in non_goals:
        problems.append("protocol capabilities must keep no_pptxgenjs_dependency non-goal")


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

    package_problems: list[str] = []
    if not missing_files and not missing_phrases:
        _validate_package_json(repo_root, package_problems)
        _validate_frontend_package(repo_root, package_problems)
        _run_package_scripts(repo_root, package_problems)

    status = "ready" if not missing_files and not missing_phrases and not package_problems else "blocked"
    return {
        "schema_version": "kw_renderer_worker_package_check.v1",
        "status": status,
        "missing_files": missing_files,
        "missing_phrases": missing_phrases,
        "package_problems": package_problems,
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
        print(f"kw_renderer_worker_package_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
