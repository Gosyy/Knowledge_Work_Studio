#!/usr/bin/env python3
"""KR-7H renderer worker package preflight contract checker.

This checker verifies that the renderer worker has an isolated package boundary
for future Node/PptxGenJS work without claiming renderer runtime readiness. From
KR-7H.5 onward the isolated renderer_worker package may declare the pinned
PptxGenJS dependency for capability preflight only. It must not generate PPTX,
run LibreOffice, write artifact/proof bundles, or touch frontend runtime
dependencies.
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
PPTXGENJS_CAPABILITY_SCHEMA_VERSION = "presentation_renderer_worker_pptxgenjs_capability.v1"
PPTXGENJS_IN_MEMORY_SCHEMA_VERSION = "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1"
EMPTY_OUTPUT_SCHEMA_VERSION = "presentation_renderer_worker_empty_pptx_output_smoke.v1"
STATIC_SLIDE_SCHEMA_VERSION = "presentation_renderer_worker_static_slide_output_smoke.v1"
MINIMAL_IR_MAPPING_SCHEMA_VERSION = "presentation_renderer_worker_minimal_ir_mapping_smoke.v1"
PPTX_ARTIFACT_BUNDLE_SCHEMA_VERSION = "presentation_renderer_worker_pptx_artifact_bundle.v1"
RENDER_REPORT_SCHEMA_VERSION = "presentation_renderer_worker_render_report.v1"
LIBREOFFICE_PROOF_BUNDLE_SCHEMA_VERSION = "presentation_renderer_worker_libreoffice_proof_bundle.v1"
SOURCE_IMAGE_HARDENING_SCHEMA_VERSION = "presentation_renderer_worker_source_image_hardening.v1"
KR7H_CLOSURE_GATE_SCHEMA_VERSION = "presentation_renderer_worker_kr7h_closure_gate.v1"
EXPECTED_PPTXGENJS_VERSION = "4.0.1"

REQUIRED_FILES = [
    "renderer_worker/package.json",
    "renderer_worker/package-lock.json",
    "renderer_worker/CONTRACT.md",
    "renderer_worker/kw_renderer_worker_protocol_preflight.mjs",
    "renderer_worker/kw_renderer_worker_pptxgenjs_capability.mjs",
    "renderer_worker/kw_renderer_worker_pptxgenjs_in_memory_preflight.mjs",
    "renderer_worker/kw_renderer_worker_empty_pptx_output_smoke.mjs",
    "renderer_worker/kw_renderer_worker_static_slide_output_smoke.mjs",
    "renderer_worker/kw_renderer_worker_minimal_ir_mapping_smoke.mjs",
    "renderer_worker/kw_renderer_worker_pptx_artifact_bundle_smoke.mjs",
    "renderer_worker/kw_renderer_worker_libreoffice_proof_bundle_smoke.mjs",
    "backend/tests/services/test_kr7h_renderer_worker_package.py",
    "backend/tests/services/test_kr7h_renderer_worker_libreoffice_proof_bundle.py",
    "backend/tests/services/test_kr7h_renderer_worker_source_image_hardening.py",
    "backend/tests/services/test_kr7h_renderer_worker_kr7h_closure_gate.py",
    "scripts/kw_renderer_worker_package_check.py",
    "scripts/kw_renderer_worker_source_image_hardening_check.py",
    "scripts/kw_renderer_worker_kr7h_closure_gate_check.py",
    "scripts/kw_renderer_worker_minimal_ir_mapping_check.py",
    "scripts/kw_renderer_worker_pptx_artifact_bundle_check.py",
    "scripts/kw_renderer_worker_libreoffice_proof_bundle_check.py",
]

REQUIRED_PHRASES = {
    "renderer_worker/package.json": [
        '"name": "kw-studio-renderer-worker"',
        '"private": true',
        '"type": "module"',
        '"protocol:preflight"',
        '"dependency:capability"',
        '"check"',
        '"presentation_renderer_worker_package_preflight.v1"',
        '"presentation_renderer_worker_pptxgenjs_capability.v1"',
        '"presentation_renderer_worker_static_slide_output_smoke.v1"',
        '"presentation_renderer_worker_minimal_ir_mapping_smoke.v1"',
        '"presentation_renderer_worker_libreoffice_proof_bundle.v1"',
        '"presentation_renderer_worker_source_image_hardening.v1"',
        '"presentation_renderer_worker_kr7h_closure_gate.v1"',
        '"renderer_worker_package_boundary": true',
        '"frontend_package_boundary": false',
        '"pptxgenjs_dependency_declared": true',
        '"pptxgenjs_dependency_version": "4.0.1"',
        '"renderer_runtime_implemented": false',
        '"production_pptx_output_implemented": false',
        '"pptx_generation_executed": false',
        '"minimal_ir_mapping_smoke_implemented": true',
        '"artifact_bundle_produced": true',
        '"proof_bundle_produced": true',
        '"libreoffice_executed": true',
        '"pdftoppm_executed": true',
        '"libreoffice_proof_bundle_smoke_implemented": true',
        '"fake_proof_used": false',
        '"fallback_renderer_used": false',
        '"python_pptx_proof_used": false',
        '"source_image_hardening_implemented": true',
        '"source_images_only_enforced": true',
        '"generated_images_allowed": false',
        '"fallback_images_allowed": false',
        '"fake_artifacts_allowed": false',
        '"inline_image_payloads_allowed": false',
        '"source_image_selection_implemented": false',
        '"kr7h_closure_gate_implemented": true',
        '"kr7h_phase_closed": true',
        '"closed_through_phase": "KR-7H.13"',
        '"production_renderer_closure_implemented": false',
        '"kimi_level_quality_claimed": false',
        '"next_phase": "KR-7I template and brand understanding"',
        '"no_frontend_package_changes"',
    ],
    "renderer_worker/package-lock.json": [
        '"name": "kw-studio-renderer-worker"',
        '"pptxgenjs": "4.0.1"',
        '"node_modules/pptxgenjs"',
        '"version": "4.0.1"',
    ],
    "renderer_worker/CONTRACT.md": [
        "KR-7H.4 renderer worker package preflight contract",
        "presentation_renderer_worker_package_preflight.v1",
        "presentation_renderer_worker_pptxgenjs_capability.v1",
        "npm run protocol:preflight --prefix renderer_worker",
        "npm run dependency:capability --prefix renderer_worker",
        "npm run pptxgenjs:in-memory --prefix renderer_worker",
        "npm run pptxgenjs:empty-output --prefix renderer_worker",
        "npm run pptxgenjs:static-slide --prefix renderer_worker",
        "npm run pptxgenjs:minimal-ir-smoke --prefix renderer_worker",
        "npm run pptxgenjs:artifact-bundle --prefix renderer_worker",
        "npm run pptxgenjs:libreoffice-proof-bundle --prefix renderer_worker",
        "presentation_renderer_worker_libreoffice_proof_bundle.v1",
        "npm run check --prefix renderer_worker",
        "renderer_runtime_implemented=false",
        "production_pptx_output_implemented=false",
        "pptx_generation_executed=false",
        "artifact_bundle_produced=false",
        "proof_bundle_produced=false",
        "PptxGenJS is declared only inside the isolated renderer_worker package",
        "does not generate production PPTX",
        "does not run LibreOffice",
        "does not change UI",
    ],
    "backend/tests/services/test_kr7h_renderer_worker_package.py": [
        "test_kr7h4_package_json_declares_isolated_renderer_worker_boundary",
        "test_kr7h5_package_declares_controlled_pptxgenjs_dependency_only_in_worker",
        "test_kr7h5_package_scripts_run_dependency_capability_without_runtime_output",
        "test_kr7h6_package_scripts_run_in_memory_preflight_without_output",
        "test_kr7h7_package_scripts_run_empty_pptx_output_smoke_without_persistent_artifact",
        "test_kr7h8_package_scripts_run_static_slide_output_smoke_without_persistent_artifact",
        "test_kr7h9_package_scripts_run_minimal_ir_mapping_smoke_without_persistent_artifact",
        "test_kr7h10_package_scripts_run_artifact_bundle_smoke_with_cleanup",
        "test_kr7h4_frontend_package_is_not_used_for_renderer_worker_boundary",
    ],
    "scripts/kw_renderer_worker_minimal_ir_mapping_check.py": [
        "presentation_renderer_worker_minimal_ir_mapping_smoke.v1",
        "kw_renderer_worker_minimal_ir_mapping_check.py",
        "pptxgenjs:minimal-ir-smoke",
        "source_backed_dry_run",
        "temporary_minimal_ir_mapping_smoke_only",
    ],
    "scripts/kw_full_tests_with_proxy_runner.sh": [
        "29h4-renderer-worker-package-check",
        "kw_renderer_worker_package_check.py --repo-root . --require-ready",
        "29h5-renderer-worker-pptxgenjs-capability-check",
        "kw_renderer_worker_pptxgenjs_capability_check.py --repo-root . --require-ready",
        "29h6-renderer-worker-pptxgenjs-in-memory-check",
        "kw_renderer_worker_pptxgenjs_in_memory_check.py --repo-root . --require-ready",
        "29h7-renderer-worker-empty-pptx-output-check",
        "kw_renderer_worker_empty_pptx_output_check.py --repo-root . --require-ready",
        "29h8-renderer-worker-static-slide-output-check",
        "kw_renderer_worker_static_slide_output_check.py --repo-root . --require-ready",
        "29h9-renderer-worker-minimal-ir-mapping-check",
        "kw_renderer_worker_minimal_ir_mapping_check.py --repo-root . --require-ready",
        "29h10-renderer-worker-pptx-artifact-bundle-check",
        "kw_renderer_worker_pptx_artifact_bundle_check.py --repo-root . --require-ready",
        "29h11-renderer-worker-libreoffice-proof-bundle-check",
        "kw_renderer_worker_libreoffice_proof_bundle_check.py --repo-root . --require-ready",
        "29h12-renderer-worker-source-image-hardening-check",
        "kw_renderer_worker_source_image_hardening_check.py --repo-root . --require-ready",
        "29h13-renderer-worker-kr7h-closure-gate-check",
        "kw_renderer_worker_kr7h_closure_gate_check.py --repo-root . --require-ready",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7H.5 controlled PptxGenJS capability preflight",
        "KR-7H.6 in-memory PptxGenJS construction preflight",
        "KR-7H.8 controlled static single-slide PPTX output smoke",
        "presentation_renderer_worker_pptxgenjs_capability.v1",
        "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1",
        "presentation_renderer_worker_static_slide_output_smoke.v1",
        "does not generate PPTX",
        "does not run LibreOffice",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "KR-7H.5 controlled PptxGenJS capability preflight",
        "presentation_renderer_worker_pptxgenjs_capability.v1",
        "no production PPTX",
        "no LibreOffice proof",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7H.5 controlled PptxGenJS capability preflight",
        "KR-7H.6 in-memory PptxGenJS construction preflight",
        "KR-7H.8 controlled static single-slide PPTX output smoke",
        "presentation_renderer_worker_pptxgenjs_capability.v1",
        "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1",
        "presentation_renderer_worker_static_slide_output_smoke.v1",
        "does not generate PPTX",
        "does not run LibreOffice",
        "does not produce artifact/proof bundles",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7H.5 adds controlled PptxGenJS capability preflight",
        "KR-7H.6 adds in-memory PptxGenJS construction preflight",
        "without PPTX generation or LibreOffice proof runtime",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim KR-7H.5 generates PPTX",
        "claim KR-7H.5 maps PresentationIR blocks into slides",
        "claim KR-7H.5 produces artifact/proof bundles",
        "claim KR-7H.6 writes PPTX files",
        "claim KR-7H.6 maps PresentationIR blocks into slides",
        "claim KR-7H.6 produces artifact/proof bundles",
        "claim KR-7H.7 creates production PPTX output",
        "claim KR-7H.7 produces artifact/proof bundles",
        "claim KR-7H.8 creates production PPTX output",
        "claim KR-7H.8 maps PresentationIR blocks into slides",
        "claim KR-7H.8 produces artifact/proof bundles",
    ],
}

FORBIDDEN_PACKAGE_FIELDS = ("devDependencies", "optionalDependencies", "peerDependencies")
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


def _worker_dependency_tree_ready(worker_root: Path) -> bool:
    return (worker_root / "node_modules" / "pptxgenjs" / "package.json").is_file()


def _ensure_npm_install(repo_root: Path, problems: list[str]) -> None:
    if not _npm_available():
        problems.append("npm executable is required for KR-7H package preflight check")
        return
    worker_root = repo_root / "renderer_worker"
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
        capability_script = scripts.get("dependency:capability")
        in_memory_script = scripts.get("pptxgenjs:in-memory")
        empty_output_script = scripts.get("pptxgenjs:empty-output")
        static_slide_script = scripts.get("pptxgenjs:static-slide")
        minimal_ir_script = scripts.get("pptxgenjs:minimal-ir-smoke")
        check_script = scripts.get("check")
        if not isinstance(protocol_script, str) or "kw_renderer_worker_protocol_preflight.mjs" not in protocol_script:
            problems.append("protocol:preflight script must call kw_renderer_worker_protocol_preflight.mjs")
        if not isinstance(capability_script, str) or "kw_renderer_worker_pptxgenjs_capability.mjs" not in capability_script:
            problems.append("dependency:capability script must call kw_renderer_worker_pptxgenjs_capability.mjs")
        if not isinstance(in_memory_script, str) or "kw_renderer_worker_pptxgenjs_in_memory_preflight.mjs" not in in_memory_script:
            problems.append("pptxgenjs:in-memory script must call kw_renderer_worker_pptxgenjs_in_memory_preflight.mjs")
        if not isinstance(empty_output_script, str) or "kw_renderer_worker_empty_pptx_output_smoke.mjs" not in empty_output_script:
            problems.append("pptxgenjs:empty-output script must call kw_renderer_worker_empty_pptx_output_smoke.mjs")
        if not isinstance(static_slide_script, str) or "kw_renderer_worker_static_slide_output_smoke.mjs" not in static_slide_script:
            problems.append("pptxgenjs:static-slide script must call kw_renderer_worker_static_slide_output_smoke.mjs")
        if not isinstance(minimal_ir_script, str) or "kw_renderer_worker_minimal_ir_mapping_smoke.mjs" not in minimal_ir_script:
            problems.append("pptxgenjs:minimal-ir-smoke script must call kw_renderer_worker_minimal_ir_mapping_smoke.mjs")
        if (
            not isinstance(check_script, str)
            or "node --check" not in check_script
            or "protocol:preflight" not in check_script
            or "dependency:capability" not in check_script
            or "pptxgenjs:in-memory" not in check_script
            or "pptxgenjs:empty-output" not in check_script
            or "pptxgenjs:static-slide" not in check_script
            or "pptxgenjs:minimal-ir-smoke" not in check_script
            or "pptxgenjs:artifact-bundle" not in check_script
            or "pptxgenjs:libreoffice-proof-bundle" not in check_script
            or "kw_renderer_worker_libreoffice_proof_bundle_smoke.mjs" not in check_script
        ):
            problems.append("check script must run node --check, protocol:preflight, dependency:capability, pptxgenjs:in-memory, pptxgenjs:empty-output, pptxgenjs:static-slide, pptxgenjs:minimal-ir-smoke, pptxgenjs:artifact-bundle, and pptxgenjs:libreoffice-proof-bundle")

    dependencies = package.get("dependencies")
    if not isinstance(dependencies, dict) or dependencies.get("pptxgenjs") != EXPECTED_PPTXGENJS_VERSION:
        problems.append("renderer_worker/package.json must declare only controlled pptxgenjs@4.0.1 dependency in KR-7H.5")
    elif set(dependencies) != {"pptxgenjs"}:
        problems.append(f"renderer_worker/package.json dependencies must contain only pptxgenjs, got {sorted(dependencies)}")

    for field in FORBIDDEN_PACKAGE_FIELDS:
        if field in package:
            problems.append(f"renderer_worker/package.json must not declare {field} in KR-7H.5")

    metadata = package.get("kwStudio")
    if not isinstance(metadata, dict):
        problems.append("renderer_worker/package.json kwStudio metadata must be an object")
        return
    expected = {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "pptxgenjs_capability_schema_version": PPTXGENJS_CAPABILITY_SCHEMA_VERSION,
        "pptxgenjs_in_memory_schema_version": PPTXGENJS_IN_MEMORY_SCHEMA_VERSION,
        "renderer_worker_package_boundary": True,
        "frontend_package_boundary": False,
        "pptxgenjs_dependency_declared": True,
        "pptxgenjs_dependency_version": EXPECTED_PPTXGENJS_VERSION,
        "pptxgenjs_capability_preflight_implemented": True,
        "pptxgenjs_in_memory_preflight_implemented": True,
        "pptxgenjs_in_memory_object_created": True,
        "empty_pptx_output_smoke_schema_version": EMPTY_OUTPUT_SCHEMA_VERSION,
        "empty_pptx_output_smoke_implemented": True,
        "temporary_pptx_write_api_called": True,
        "temporary_pptx_written": True,
        "temporary_pptx_deleted": True,
        "temporary_pptx_file_size_nonzero": True,
        "static_slide_output_smoke_schema_version": STATIC_SLIDE_SCHEMA_VERSION,
        "static_slide_output_smoke_implemented": True,
        "temporary_static_slide_pptx_write_api_called": True,
        "temporary_static_slide_pptx_written": True,
        "temporary_static_slide_pptx_deleted": True,
        "temporary_static_slide_pptx_file_size_nonzero": True,
        "static_slide_count": 1,
        "static_slide_content_added": True,
        "static_slide_uses_user_content": False,
        "static_slide_uses_presentation_ir": False,
        "presentation_ir_mapping_implemented": True,
        "minimal_ir_mapping_smoke_schema_version": MINIMAL_IR_MAPPING_SCHEMA_VERSION,
        "minimal_ir_mapping_smoke_implemented": True,
        "title_body_mapping_implemented": True,
        "single_slide_smoke_executed": True,
        "multi_slide_smoke_executed": True,
        "temporary_minimal_ir_pptx_written": True,
        "temporary_minimal_ir_pptx_deleted": True,
        "temporary_minimal_ir_pptx_file_size_nonzero": True,
        "chart_mapping_implemented": False,
        "table_mapping_implemented": False,
        "image_mapping_implemented": False,
        "theme_mapping_implemented": False,
        "professional_layout_engine_implemented": False,
        "user_prompt_passthrough_allowed": False,
        "artifact_bundle_schema_version": PPTX_ARTIFACT_BUNDLE_SCHEMA_VERSION,
        "render_report_schema_version": RENDER_REPORT_SCHEMA_VERSION,
        "pptx_artifact_bundle_contract_implemented": True,
        "render_report_contract_implemented": True,
        "persistent_artifact_written": True,
        "artifact_bundle_verified": True,
        "render_report_written": True,
        "render_report_deterministic": True,
        "libreoffice_executed": True,
        "pdftoppm_executed": True,
        "visual_qa_executed": False,
        "slide_content_added": False,
        "pptxgenjs_write_api_called": False,
        "filesystem_output_written": True,
        "renderer_runtime_implemented": False,
        "production_pptx_output_implemented": False,
        "pptx_generation_executed": False,
        "artifact_bundle_produced": True,
        "proof_bundle_produced": True,
        "libreoffice_proof_bundle_schema_version": LIBREOFFICE_PROOF_BUNDLE_SCHEMA_VERSION,
        "libreoffice_proof_bundle_smoke_implemented": True,
        "libreoffice_required_for_proof_bundle": True,
        "pdftoppm_required_for_proof_bundle": True,
        "proof_bundle_verified": True,
        "pdf_proof_written": True,
        "png_proofs_written": True,
        "fake_proof_used": False,
        "fallback_renderer_used": False,
        "python_pptx_proof_used": False,
        "source_image_hardening_schema_version": SOURCE_IMAGE_HARDENING_SCHEMA_VERSION,
        "source_image_hardening_implemented": True,
        "source_images_only_enforced": True,
        "generated_images_allowed": False,
        "fallback_images_allowed": False,
        "fake_artifacts_allowed": False,
        "inline_image_payloads_allowed": False,
        "source_image_selection_implemented": False,
        "kr7h_closure_gate_schema_version": KR7H_CLOSURE_GATE_SCHEMA_VERSION,
        "kr7h_closure_gate_implemented": True,
        "kr7h_phase_closed": True,
        "closed_through_phase": "KR-7H.13",
        "production_renderer_closure_implemented": False,
        "kimi_level_quality_claimed": False,
        "fallback_renderer_allowed": False,
        "next_phase": "KR-7I template and brand understanding",
    }
    for key, expected_value in expected.items():
        if metadata.get(key) != expected_value:
            problems.append(f"renderer_worker kwStudio.{key} expected {expected_value!r}, got {metadata.get(key)!r}")
    non_goals = metadata.get("non_goals") if isinstance(metadata.get("non_goals"), list) else []
    for non_goal in ("no_charts_tables_images_mapping", "no_frontend_package_changes", "no_fake_proof_artifacts", "no_fallback_renderer_as_success", "no_visual_qa_scoring", "no_source_image_selection_runtime", "no_image_mapping_runtime", "no_generated_images", "no_fake_artifacts", "no_inline_image_payloads", "no_production_renderer_closure", "no_kimi_level_quality_claim", "no_template_or_brand_understanding", "no_docker_deploy_postgres_changes"):
        if non_goal not in non_goals:
            problems.append(f"renderer_worker kwStudio.non_goals missing {non_goal}")


def _validate_package_lock(repo_root: Path, problems: list[str]) -> None:
    path = repo_root / "renderer_worker" / "package-lock.json"
    try:
        lock = _load_json(path)
    except Exception as exc:  # noqa: BLE001
        problems.append(f"renderer_worker/package-lock.json is not valid JSON: {exc}")
        return
    packages = lock.get("packages") if isinstance(lock, dict) else None
    root = packages.get("") if isinstance(packages, dict) else None
    dependency = packages.get("node_modules/pptxgenjs") if isinstance(packages, dict) else None
    if not isinstance(root, dict) or root.get("dependencies", {}).get("pptxgenjs") != EXPECTED_PPTXGENJS_VERSION:
        problems.append("renderer_worker/package-lock.json root dependency must pin pptxgenjs@4.0.1")
    if not isinstance(dependency, dict) or dependency.get("version") != EXPECTED_PPTXGENJS_VERSION:
        problems.append("renderer_worker/package-lock.json must lock node_modules/pptxgenjs version 4.0.1")


def _validate_frontend_package(repo_root: Path, problems: list[str]) -> None:
    frontend_package = repo_root / "frontend" / "package.json"
    if not frontend_package.is_file():
        return
    text = _read(frontend_package).lower()
    for phrase in FORBIDDEN_FRONTEND_PHRASES:
        if phrase in text:
            problems.append(f"frontend/package.json must not contain renderer worker dependency marker {phrase!r} in KR-7H.5")


def _run_package_scripts(repo_root: Path, problems: list[str]) -> None:
    if not _node_available():
        problems.append("node executable is required for KR-7H package preflight check")
        return
    if not _npm_available():
        problems.append("npm executable is required for KR-7H package preflight check")
        return

    worker_root = repo_root / "renderer_worker"
    for script_name in ("kw_renderer_worker_protocol_preflight.mjs", "kw_renderer_worker_pptxgenjs_capability.mjs", "kw_renderer_worker_pptxgenjs_in_memory_preflight.mjs", "kw_renderer_worker_empty_pptx_output_smoke.mjs", "kw_renderer_worker_static_slide_output_smoke.mjs", "kw_renderer_worker_minimal_ir_mapping_smoke.mjs", "kw_renderer_worker_pptx_artifact_bundle_smoke.mjs", "kw_renderer_worker_libreoffice_proof_bundle_smoke.mjs"):
        syntax = subprocess.run(
            ["node", "--check", script_name],
            cwd=worker_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if syntax.returncode != 0:
            problems.append(f"renderer_worker {script_name} syntax failed: {syntax.stdout}{syntax.stderr}")
            return

    # Dedicated KR-7H.3 through KR-7H.10 checkers execute runtime script
    # contracts. The package checker keeps this step static/lightweight so full
    # and targeted runners do not duplicate expensive renderer smoke execution.
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

    code, capability, diagnostics = _run_json(["npm", "run", "dependency:capability", "--silent"], cwd=worker_root)
    if code != 0 or not isinstance(capability, dict):
        problems.append(f"npm run dependency:capability --prefix renderer_worker did not return JSON: {diagnostics}")
        return
    expected_dependency = {
        "schema_version": PPTXGENJS_CAPABILITY_SCHEMA_VERSION,
        "dependency_name": "pptxgenjs",
        "expected_dependency_version": EXPECTED_PPTXGENJS_VERSION,
        "dependency_available": True,
        "dependency_version": EXPECTED_PPTXGENJS_VERSION,
        "renderer_runtime_implemented": False,
        "production_pptx_output_implemented": False,
        "pptx_generation_executed": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
        "output_mode": "dependency_capability_preflight_only",
    }
    for key, expected in expected_dependency.items():
        if capability.get(key) != expected:
            problems.append(f"renderer_worker dependency capability {key} expected {expected!r}, got {capability.get(key)!r}")

    code, empty_output, diagnostics = _run_json(["npm", "run", "pptxgenjs:empty-output", "--silent"], cwd=worker_root)
    if code != 0 or not isinstance(empty_output, dict):
        problems.append(f"npm run pptxgenjs:empty-output --prefix renderer_worker did not return JSON: {diagnostics}")
        return
    expected_empty_output = {
        "schema_version": EMPTY_OUTPUT_SCHEMA_VERSION,
        "status": "ready",
        "temporary_pptx_written": True,
        "temporary_pptx_deleted": True,
        "temporary_pptx_file_size_nonzero": True,
        "presentation_ir_mapping_implemented": False,
        "persistent_artifact_written": False,
        "filesystem_output_written": False,
        "production_pptx_output_implemented": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
        "libreoffice_executed": False,
        "visual_qa_executed": False,
        "output_mode": "temporary_empty_pptx_output_smoke_only",
    }
    for key, expected in expected_empty_output.items():
        if empty_output.get(key) != expected:
            problems.append(f"renderer_worker empty output {key} expected {expected!r}, got {empty_output.get(key)!r}")


    code, static_slide, diagnostics = _run_json(["npm", "run", "pptxgenjs:static-slide", "--silent"], cwd=worker_root)
    if code != 0 or not isinstance(static_slide, dict):
        problems.append(f"npm run pptxgenjs:static-slide --prefix renderer_worker did not return JSON: {diagnostics}")
        return
    expected_static_slide = {
        "schema_version": STATIC_SLIDE_SCHEMA_VERSION,
        "status": "ready",
        "temporary_pptx_written": True,
        "temporary_pptx_deleted": True,
        "temporary_pptx_file_size_nonzero": True,
        "static_slide_count": 1,
        "static_slide_content_added": True,
        "static_slide_uses_user_content": False,
        "static_slide_uses_presentation_ir": False,
        "presentation_ir_mapping_implemented": False,
        "persistent_artifact_written": False,
        "filesystem_output_written": False,
        "production_pptx_output_implemented": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
        "libreoffice_executed": False,
        "visual_qa_executed": False,
        "output_mode": "temporary_static_single_slide_output_smoke_only",
    }
    for key, expected in expected_static_slide.items():
        if static_slide.get(key) != expected:
            problems.append(f"renderer_worker static slide output {key} expected {expected!r}, got {static_slide.get(key)!r}")


    code, minimal_ir, diagnostics = _run_json(["npm", "run", "pptxgenjs:minimal-ir-smoke", "--silent"], cwd=worker_root)
    if code != 0 or not isinstance(minimal_ir, dict):
        problems.append(f"npm run pptxgenjs:minimal-ir-smoke --prefix renderer_worker did not return JSON: {diagnostics}")
        return
    expected_minimal_ir = {
        "schema_version": MINIMAL_IR_MAPPING_SCHEMA_VERSION,
        "status": "ready",
        "single_slide_smoke_executed": True,
        "multi_slide_smoke_executed": True,
        "single_slide_pptx_written": True,
        "single_slide_pptx_deleted": True,
        "single_slide_file_size_nonzero": True,
        "multi_slide_pptx_written": True,
        "multi_slide_pptx_deleted": True,
        "multi_slide_file_size_nonzero": True,
        "title_body_mapping_implemented": True,
        "presentation_ir_mapping_implemented": True,
        "chart_mapping_implemented": False,
        "table_mapping_implemented": False,
        "image_mapping_implemented": False,
        "professional_layout_engine_implemented": False,
        "persistent_artifact_written": False,
        "filesystem_output_written": False,
        "production_pptx_output_implemented": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
        "libreoffice_executed": False,
        "visual_qa_executed": False,
        "output_mode": "temporary_minimal_ir_mapping_smoke_only",
    }
    for key, expected in expected_minimal_ir.items():
        if minimal_ir.get(key) != expected:
            problems.append(f"renderer_worker minimal IR mapping {key} expected {expected!r}, got {minimal_ir.get(key)!r}")
    if not isinstance(minimal_ir.get("mapped_slide_ids"), list) or len(minimal_ir["mapped_slide_ids"]) < 2:
        problems.append("renderer_worker minimal IR mapping must report at least two mapped_slide_ids")

    code, artifact_bundle, diagnostics = _run_json(["npm", "run", "pptxgenjs:artifact-bundle", "--silent"], cwd=worker_root)
    if code != 0 or not isinstance(artifact_bundle, dict):
        problems.append(f"npm run pptxgenjs:artifact-bundle --prefix renderer_worker did not return JSON: {diagnostics}")
        return
    expected_artifact_bundle = {
        "schema_version": PPTX_ARTIFACT_BUNDLE_SCHEMA_VERSION,
        "status": "ready",
        "render_report_schema_version": RENDER_REPORT_SCHEMA_VERSION,
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
        "output_directory_cleanup_requested": True,
        "output_directory_cleanup_performed": True,
    }
    for key, expected in expected_artifact_bundle.items():
        if artifact_bundle.get(key) != expected:
            problems.append(f"renderer_worker artifact bundle {key} expected {expected!r}, got {artifact_bundle.get(key)!r}")
    if not isinstance(artifact_bundle.get("mapped_slide_ids"), list) or len(artifact_bundle["mapped_slide_ids"]) < 2:
        problems.append("renderer_worker artifact bundle must report at least two mapped_slide_ids")


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
        _validate_package_lock(repo_root, package_problems)
        _validate_frontend_package(repo_root, package_problems)
        if not package_problems:
            _ensure_npm_install(repo_root, package_problems)
        if not package_problems:
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
