#!/usr/bin/env python3
"""KR-7H.8 controlled static single-slide PPTX output smoke checker.

This checker verifies that the isolated renderer_worker package can write a
controlled temporary PPTX containing one fixed technical smoke slide, delete it,
and return a fail-closed report without claiming production renderer readiness.
It must not map PresentationIR blocks, use user/evidence content, persist
artifacts, run LibreOffice, write proof bundles, or perform visual QA.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "presentation_renderer_worker_static_slide_output_smoke.v1"
EXPECTED_VERSION = "4.0.1"

REQUIRED_FILES = [
    "renderer_worker/package.json",
    "renderer_worker/package-lock.json",
    "renderer_worker/CONTRACT.md",
    "renderer_worker/kw_renderer_worker_static_slide_output_smoke.mjs",
    "backend/tests/services/test_kr7h_renderer_worker_static_slide_output.py",
    "scripts/kw_renderer_worker_static_slide_output_check.py",
]

REQUIRED_PHRASES = {
    "renderer_worker/package.json": [
        '"pptxgenjs:static-slide"',
        '"presentation_renderer_worker_static_slide_output_smoke.v1"',
        '"static_slide_output_smoke_implemented": true',
        '"temporary_static_slide_pptx_write_api_called": true',
        '"temporary_static_slide_pptx_written": true',
        '"temporary_static_slide_pptx_deleted": true',
        '"temporary_static_slide_pptx_file_size_nonzero": true',
        '"static_slide_count": 1',
        '"static_slide_content_added": true',
        '"static_slide_uses_user_content": false',
        '"static_slide_uses_presentation_ir": false',
        '"renderer_runtime_implemented": false',
        '"production_pptx_output_implemented": false',
        '"proof_bundle_produced": false',
        '"libreoffice_executed": false',
        '"visual_qa_executed": false',
    ],
    "renderer_worker/CONTRACT.md": [
        "KR-7H.8 extends that boundary with a controlled static single-slide PPTX output smoke",
        "presentation_renderer_worker_static_slide_output_smoke.v1",
        "npm run pptxgenjs:static-slide --prefix renderer_worker",
        "static_slide_count=1",
        "static_slide_content_added=true",
        "static_slide_uses_user_content=false",
        "static_slide_uses_presentation_ir=false",
        "persistent_artifact_written=false",
        "presentation_ir_mapping_implemented=false",
        "production_pptx_output_implemented=false",
    ],
    "renderer_worker/kw_renderer_worker_static_slide_output_smoke.mjs": [
        "presentation_renderer_worker_static_slide_output_smoke.v1",
        "KW Studio Renderer Worker Smoke",
        "KR-7H.8 static slide output smoke only",
        "presentation.addSlide()",
        "slide.addText(STATIC_TITLE",
        "writeFile({ fileName: outputPath })",
        "temporary_static_single_slide_output_smoke_only",
        "static_slide_count",
        "static_slide_content_added",
        "static_slide_uses_user_content: false",
        "static_slide_uses_presentation_ir: false",
        "persistent_artifact_written: false",
        "filesystem_output_written: false",
        "libreoffice_executed: false",
        "visual_qa_executed: false",
    ],
    "backend/tests/services/test_kr7h_renderer_worker_static_slide_output.py": [
        "test_kr7h8_static_slide_output_smoke_writes_and_deletes_temporary_pptx",
        "test_kr7h8_static_slide_output_smoke_uses_only_fixed_technical_content",
        "test_kr7h8_package_check_runs_static_slide_output_without_frontend_changes",
    ],
    "scripts/kw_full_tests_with_proxy_runner.sh": [
        "29h8-renderer-worker-static-slide-output-check",
        "kw_renderer_worker_static_slide_output_check.py --repo-root . --require-ready",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7H.8 controlled static single-slide PPTX output smoke",
        "presentation_renderer_worker_static_slide_output_smoke.v1",
        "static_slide_count=1",
        "static_slide_uses_user_content=false",
        "does not map PresentationIR blocks into slides",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "KR-7H.8 controlled static single-slide PPTX output smoke",
        "fixed technical smoke slide",
        "no PresentationIR mapping",
        "no persistent artifact",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7H.8 controlled static single-slide PPTX output smoke",
        "presentation_renderer_worker_static_slide_output_smoke.v1",
        "static_slide_count=1",
        "static_slide_uses_user_content=false",
        "does not produce artifact/proof bundles",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7H.8 adds controlled static single-slide PPTX output smoke",
        "fixed technical smoke slide",
        "without PresentationIR mapping, persistent artifacts, or LibreOffice proof runtime",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim KR-7H.8 creates production PPTX output",
        "claim KR-7H.8 maps PresentationIR blocks into slides",
        "claim KR-7H.8 uses user prompt or evidence content",
        "claim KR-7H.8 produces artifact/proof bundles",
    ],
}

FORBIDDEN_TEXT = {
    "renderer_worker/kw_renderer_worker_static_slide_output_smoke.mjs": [
        "runLibreOffice",
        "artifact_bundle_produced: true",
        "proof_bundle_produced: true",
        "persistent_artifact_written: true",
        "production_pptx_output_implemented: true",
        "static_slide_uses_user_content: true",
        "static_slide_uses_presentation_ir: true",
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
        "static_slide_output_smoke_schema_version": SCHEMA_VERSION,
        "static_slide_output_smoke_implemented": True,
        "temporary_static_slide_pptx_write_api_called": True,
        "temporary_static_slide_pptx_written": True,
        "temporary_static_slide_pptx_deleted": True,
        "temporary_static_slide_pptx_file_size_nonzero": True,
        "static_slide_count": 1,
        "static_slide_content_added": True,
        "static_slide_uses_user_content": False,
        "static_slide_uses_presentation_ir": False,
        "renderer_runtime_implemented": False,
        "production_pptx_output_implemented": False,
        "proof_bundle_produced": False,
        "libreoffice_executed": False,
        "visual_qa_executed": False,
    }
    for key, expected_value in expected.items():
        if metadata.get(key) != expected_value:
            problems.append(f"kwStudio.{key} expected {expected_value!r}, got {metadata.get(key)!r}")
    scripts = package.get("scripts") if isinstance(package.get("scripts"), dict) else {}
    if "kw_renderer_worker_static_slide_output_smoke.mjs" not in str(scripts.get("pptxgenjs:static-slide", "")):
        problems.append("renderer_worker/package.json must define pptxgenjs:static-slide script")
    if "pptxgenjs:static-slide" not in str(scripts.get("check", "")):
        problems.append("renderer_worker/package.json check script must run pptxgenjs:static-slide")


def _run_static_slide_output(repo_root: Path, problems: list[str]) -> None:
    if not _node_available():
        problems.append("node executable is required for KR-7H.8 static slide output check")
        return
    if not _npm_available():
        problems.append("npm executable is required for KR-7H.8 static slide output check")
        return
    worker_root = repo_root / "renderer_worker"
    _ensure_npm_install(worker_root, problems)
    if problems:
        return
    code, payload, diagnostics = _run_json(["npm", "run", "pptxgenjs:static-slide", "--silent"], cwd=worker_root)
    if code != 0 or not isinstance(payload, dict):
        problems.append(f"npm run pptxgenjs:static-slide --prefix renderer_worker did not return ready JSON: {diagnostics}")
        return
    expected = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "dependency_name": "pptxgenjs",
        "dependency_version": EXPECTED_VERSION,
        "static_slide_output_smoke_implemented": True,
        "temporary_pptx_write_api_called": True,
        "temporary_pptx_written": True,
        "temporary_pptx_deleted": True,
        "temporary_directory_removed": True,
        "temporary_pptx_file_size_nonzero": True,
        "static_slide_count": 1,
        "static_slide_content_added": True,
        "static_slide_title": "KW Studio Renderer Worker Smoke",
        "static_slide_subtitle": "KR-7H.8 static slide output smoke only",
        "static_slide_uses_user_content": False,
        "static_slide_uses_presentation_ir": False,
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
        "output_mode": "temporary_static_single_slide_output_smoke_only",
    }
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value:
            problems.append(f"static-slide {key} expected {expected_value!r}, got {payload.get(key)!r}")
    size = payload.get("temporary_pptx_file_size_bytes")
    if not isinstance(size, int) or size <= 0:
        problems.append(f"static-slide temporary_pptx_file_size_bytes must be positive, got {size!r}")
    if payload.get("issues") != []:
        problems.append(f"static-slide issues expected [], got {payload.get('issues')!r}")
    blocked = payload.get("blocked_runtime_actions") if isinstance(payload.get("blocked_runtime_actions"), list) else []
    for action in ("map_presentation_ir_to_slides", "use_user_prompt_content", "persist_pptx_artifact", "run_libreoffice_pdf_export", "write_artifact_bundle"):
        if action not in blocked:
            problems.append(f"static-slide blocked_runtime_actions missing {action}")


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
            _run_static_slide_output(repo_root, problems)

    status = "ready" if not missing_files and not missing_phrases and not forbidden_hits and not problems else "blocked"
    return {
        "schema_version": "kw_renderer_worker_static_slide_output_check.v1",
        "status": status,
        "missing_files": missing_files,
        "missing_phrases": missing_phrases,
        "forbidden_hits": forbidden_hits,
        "static_slide_output_problems": problems,
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
        print(f"kw_renderer_worker_static_slide_output_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
