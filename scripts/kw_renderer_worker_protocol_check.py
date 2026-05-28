#!/usr/bin/env python3
"""Validate KR-7H.3 renderer worker protocol preflight scaffold."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "renderer_worker/kw_renderer_worker_protocol_preflight.mjs",
    "backend/tests/services/test_kr7h_renderer_worker_protocol.py",
    "scripts/kw_renderer_worker_protocol_check.py",
]

REQUIRED_PHRASES = {
    "renderer_worker/kw_renderer_worker_protocol_preflight.mjs": [
        'PROTOCOL_SCHEMA_VERSION = "presentation_renderer_worker_protocol_preflight.v1"',
        'RESPONSE_SCHEMA_VERSION = "presentation_renderer_worker_protocol_preflight_response.v1"',
        'DRY_RUN_SCHEMA_VERSION = "presentation_renderer_worker_dry_run.v1"',
        'INVOCATION_MANIFEST_SCHEMA_VERSION = "presentation_renderer_worker_invocation_manifest.v1"',
        'RENDERER_INPUT_SCHEMA_VERSION = "presentation_renderer_worker_input.v1"',
        "validateDryRunPayload",
        "validateInvocationManifest",
        "validateRendererInput",
        "renderer_runtime_implemented: false",
        "production_pptx_output_implemented: false",
        "artifact_bundle_produced: false",
        "proof_bundle_produced: false",
        "import_or_execute_pptxgenjs",
        "run_libreoffice_pdf_export",
        "no_pptxgenjs_dependency",
        "no_pptx_generation",
        "protocol_preflight_only",
    ],
    "backend/tests/services/test_kr7h_renderer_worker_protocol.py": [
        "test_kr7h3_protocol_capabilities_are_preflight_only",
        "test_kr7h3_protocol_accepts_ready_dry_run_payload_without_runtime_output",
        "test_kr7h3_protocol_blocks_prompt_only_dry_run_payload",
        "test_kr7h3_protocol_rejects_runtime_and_bundle_claims",
        "test_kr7h3_protocol_rejects_invalid_json_fail_closed",
    ],
    "scripts/kw_full_tests_with_proxy_runner.sh": [
        "29h3-renderer-worker-protocol-check",
        "kw_renderer_worker_protocol_check.py --repo-root . --require-ready",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7H.3 renderer worker protocol preflight scaffold",
        "presentation_renderer_worker_protocol_preflight.v1",
        "presentation_renderer_worker_protocol_preflight_response.v1",
        "does not generate PPTX",
        "does not import or execute PptxGenJS",
        "does not run LibreOffice",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "KR-7H.3 renderer worker protocol preflight scaffold",
        "Node-side protocol preflight",
        "presentation_renderer_worker_protocol_preflight.v1",
        "no production PPTX",
        "no LibreOffice proof",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7H.3 renderer worker protocol preflight scaffold",
        "Node-side protocol preflight",
        "does not generate PPTX",
        "does not run LibreOffice",
        "does not produce artifact/proof bundles",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7H.3 adds renderer worker protocol preflight scaffold",
        "without PptxGenJS rendering or LibreOffice proof runtime",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim KR-7H.3 generates PPTX",
        "claim KR-7H.3 imports or executes PptxGenJS",
        "claim KR-7H.3 produces artifact/proof bundles",
    ],
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _node_available() -> bool:
    return shutil.which("node") is not None


def _run_json(command: list[str], *, input_text: str | None = None) -> tuple[int, dict[str, Any] | None, str]:
    completed = subprocess.run(command, input=input_text, text=True, capture_output=True, check=False)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = None
    diagnostics = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    return completed.returncode, payload, diagnostics


def _sample_ready_dry_run_payload(repo_root: Path) -> dict[str, Any]:
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

    from backend.app.services.slides_service import (  # noqa: PLC0415 - imported only for product contract check
        OfflineEvidenceIndexBuilder,
        OfflineSourceIngestionEngine,
        PresentationIRPlannerFoundation,
        PresentationIRPlannerRequest,
        build_renderer_worker_dry_run_report,
    )

    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Retention\n\nCustomer retention improved after support automation.\n\n# Risk\n\nDeployment risk decreased after rollout automation.",
        source_id="src_renderer_protocol_check",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    result = PresentationIRPlannerFoundation().plan_from_evidence(
        PresentationIRPlannerRequest(
            presentation_id="pres_kr7h3_check",
            title="Support automation results",
            objective="Support automation retention risk",
            slide_count=4,
            required_sections=("retention", "risk"),
            require_evidence=True,
        ),
        index,
    )
    if result.presentation_ir is None:
        raise RuntimeError("Planner did not return PresentationIR for KR-7H.3 protocol check.")
    dry_run = build_renderer_worker_dry_run_report(result.presentation_ir, request_id="req_protocol_check")
    return dry_run.as_dict()


def _run_protocol_checks(repo_root: Path, problems: list[str]) -> None:
    script = repo_root / "renderer_worker" / "kw_renderer_worker_protocol_preflight.mjs"
    if not _node_available():
        problems.append("node executable is required for KR-7H.3 protocol preflight check")
        return

    syntax = subprocess.run(["node", "--check", str(script)], text=True, capture_output=True, check=False)
    if syntax.returncode != 0:
        problems.append(f"node --check failed: {syntax.stdout}{syntax.stderr}")
        return

    code, capabilities, diagnostics = _run_json(["node", str(script), "--capabilities"])
    if code != 0 or not isinstance(capabilities, dict):
        problems.append(f"protocol capabilities failed: {diagnostics}")
        return
    expected_caps = {
        "schema_version": "presentation_renderer_worker_protocol_preflight.v1",
        "renderer_runtime_implemented": False,
        "production_pptx_output_implemented": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
    }
    for key, expected in expected_caps.items():
        if capabilities.get(key) != expected:
            problems.append(f"protocol capabilities {key} expected {expected!r}, got {capabilities.get(key)!r}")

    ready_payload = _sample_ready_dry_run_payload(repo_root)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        json.dump(ready_payload, handle, ensure_ascii=False)
        input_path = Path(handle.name)
    try:
        code, response, diagnostics = _run_json(["node", str(script), "--input", str(input_path)])
    finally:
        input_path.unlink(missing_ok=True)
    if code != 0 or not isinstance(response, dict):
        problems.append(f"ready protocol preflight failed: {diagnostics}")
    else:
        expected_response = {
            "schema_version": "presentation_renderer_worker_protocol_preflight_response.v1",
            "protocol_schema_version": "presentation_renderer_worker_protocol_preflight.v1",
            "status": "ready",
            "renderer_runtime_implemented": False,
            "production_pptx_output_implemented": False,
            "artifact_bundle_produced": False,
            "proof_bundle_produced": False,
            "output_mode": "protocol_preflight_only",
        }
        for key, expected in expected_response.items():
            if response.get(key) != expected:
                problems.append(f"protocol response {key} expected {expected!r}, got {response.get(key)!r}")

    blocked_payload = dict(ready_payload)
    blocked_payload["renderer_runtime_implemented"] = True
    code, response, diagnostics = _run_json(["node", str(script)], input_text=json.dumps(blocked_payload))
    if code == 0 or not isinstance(response, dict) or response.get("status") != "blocked":
        problems.append(f"blocked protocol preflight did not fail closed: {diagnostics}")


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

    protocol_problems: list[str] = []
    if not missing_files and not missing_phrases:
        _run_protocol_checks(repo_root, protocol_problems)

    status = "ready" if not missing_files and not missing_phrases and not protocol_problems else "blocked"
    return {
        "schema_version": "kw_renderer_worker_protocol_check.v1",
        "status": status,
        "missing_files": missing_files,
        "missing_phrases": missing_phrases,
        "protocol_problems": protocol_problems,
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
        print(f"kw_renderer_worker_protocol_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
