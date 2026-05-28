#!/usr/bin/env python3
"""Validate KR-7H.2 renderer worker dry-run scaffold contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "backend/app/services/slides_service/renderer_worker_dry_run.py",
    "backend/tests/services/test_kr7h_renderer_worker_dry_run.py",
    "scripts/kw_renderer_worker_dry_run_check.py",
]

REQUIRED_PHRASES = {
    "backend/app/services/slides_service/renderer_worker_dry_run.py": [
        'RENDERER_WORKER_DRY_RUN_SCHEMA_VERSION = "presentation_renderer_worker_dry_run.v1"',
        'RENDERER_WORKER_INVOCATION_MANIFEST_SCHEMA_VERSION = "presentation_renderer_worker_invocation_manifest.v1"',
        "RendererWorkerDryRunResult",
        "renderer_worker_dry_run_capabilities",
        "build_renderer_worker_dry_run_report",
        "build_renderer_worker_invocation_manifest",
        "require_renderer_worker_dry_run_ready",
        "emit_invocation_manifest_without_runtime_execution",
        "block_artifact_and_proof_bundle_production",
        "renderer_runtime_implemented",
        "artifact_bundle_produced",
        "proof_bundle_produced",
        "start_node_worker",
        "import_or_execute_pptxgenjs",
        "run_libreoffice_pdf_export",
        "no_production_quality_output_claims",
    ],
    "backend/app/services/slides_service/__init__.py": [
        "RENDERER_WORKER_DRY_RUN_SCHEMA_VERSION",
        "RENDERER_WORKER_INVOCATION_MANIFEST_SCHEMA_VERSION",
        "RendererWorkerDryRunResult",
        "renderer_worker_dry_run_capabilities",
        "build_renderer_worker_dry_run_report",
        "build_renderer_worker_invocation_manifest",
        "require_renderer_worker_dry_run_ready",
    ],
    "backend/tests/services/test_kr7h_renderer_worker_dry_run.py": [
        "test_kr7h2_dry_run_capabilities_are_contract_only",
        "test_kr7h2_dry_run_accepts_source_backed_presentation_ir_without_runtime_output",
        "test_kr7h2_dry_run_blocks_prompt_only_visual_grammar_gaps",
        "test_kr7h2_dry_run_blocks_fake_native_chart_data",
        "test_kr7h2_require_dry_run_ready_fails_closed",
    ],
    "scripts/kw_full_tests_with_proxy_runner.sh": [
        "29h2-renderer-worker-dry-run-check",
        "kw_renderer_worker_dry_run_check.py --repo-root . --require-ready",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7H.2 renderer worker dry-run scaffold contract",
        "renderer-worker dry-run report",
        "does not generate production PPTX",
        "does not start Node/PptxGenJS",
        "does not run LibreOffice",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "KR-7H.2 renderer worker dry-run scaffold contract",
        "presentation_renderer_worker_dry_run.v1",
        "presentation_renderer_worker_invocation_manifest.v1",
        "no production PPTX",
        "no Node/PptxGenJS runtime",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7H.2 renderer worker dry-run scaffold contract",
        "renderer input into a deterministic dry-run report",
        "does not generate PPTX",
        "does not run LibreOffice",
        "does not produce artifact/proof bundles",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7H.2 adds renderer worker dry-run scaffold contract",
        "without Node/PptxGenJS or LibreOffice runtime",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim KR-7H.2 generates production PPTX",
        "claim KR-7H.2 starts Node/PptxGenJS",
        "claim KR-7H.2 produces artifact/proof bundles",
    ],
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


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
    status = "ready" if not missing_files and not missing_phrases else "blocked"
    return {
        "schema_version": "kw_renderer_worker_dry_run_check.v1",
        "status": status,
        "missing_files": missing_files,
        "missing_phrases": missing_phrases,
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
        print(f"kw_renderer_worker_dry_run_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
