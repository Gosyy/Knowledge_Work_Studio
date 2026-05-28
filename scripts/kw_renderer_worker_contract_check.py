#!/usr/bin/env python3
"""Validate KR-7H.1 renderer worker boundary contract preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "backend/app/services/slides_service/renderer_worker_contract.py",
    "backend/tests/services/test_kr7h_renderer_worker_contract.py",
]

REQUIRED_PHRASES = {
    "backend/app/services/slides_service/renderer_worker_contract.py": [
        'RENDERER_WORKER_CONTRACT_SCHEMA_VERSION = "presentation_renderer_worker_contract.v1"',
        'RENDERER_WORKER_INPUT_SCHEMA_VERSION = "presentation_renderer_worker_input.v1"',
        'RENDERER_WORKER_ARTIFACT_BUNDLE_SCHEMA_VERSION = "presentation_renderer_artifact_bundle.v1"',
        'RENDERER_WORKER_PROOF_BUNDLE_SCHEMA_VERSION = "presentation_renderer_proof_bundle.v1"',
        "RENDERER_WORKER_RUNTIME_IMPLEMENTED = False",
        "renderer_worker_boundary_contract_payload",
        "build_renderer_worker_input_payload",
        "validate_renderer_worker_input_payload",
        "python_backend_builds_presentation_ir",
        "node_pptxgenjs_worker_receives_json",
        "pptxgenjs_creates_native_editable_pptx",
        "libreoffice_renders_pdf_png_proof",
        "backend_stores_artifact_and_proof_bundle",
        "declared_not_produced_by_kr7h1",
        "no_production_quality_output_claims",
        "unsupported_renderer_runtime_claim",
        "visual_grammar_binding_blocked",
        "native_chart_blocks_require_real_numeric_source_data_refs",
    ],
    "backend/app/services/slides_service/__init__.py": [
        "RENDERER_WORKER_CONTRACT_SCHEMA_VERSION",
        "RENDERER_WORKER_INPUT_SCHEMA_VERSION",
        "RENDERER_WORKER_ARTIFACT_BUNDLE_SCHEMA_VERSION",
        "RENDERER_WORKER_PROOF_BUNDLE_SCHEMA_VERSION",
        "renderer_worker_boundary_contract_payload",
        "build_renderer_worker_input_payload",
        "validate_renderer_worker_input_payload",
    ],
    "backend/tests/services/test_kr7h_renderer_worker_contract.py": [
        "test_kr7h1_renderer_worker_boundary_contract_is_contract_only",
        "test_kr7h1_renderer_worker_input_contract_accepts_source_backed_presentation_ir",
        "test_kr7h1_renderer_worker_input_blocks_prompt_only_visual_grammar_gaps",
        "test_kr7h1_renderer_worker_input_blocks_fake_native_chart_data",
        "test_kr7h1_renderer_worker_input_rejects_runtime_output_claims",
    ],
    "scripts/kw_full_tests_with_proxy_runner.sh": [
        "29h-renderer-worker-contract-check",
        "kw_renderer_worker_contract_check.py --repo-root . --require-ready",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7H.1 renderer worker boundary contract preflight",
        "Python PresentationIR -> Node/PptxGenJS renderer input -> artifact/proof bundle",
        "renderer_runtime_implemented=false",
        "do not implement production PPTX rendering in KR-7H.1",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "KR-7H.1 renderer worker boundary contract preflight",
        "presentation_renderer_worker_contract.v1",
        "presentation_renderer_worker_input.v1",
        "artifact/proof bundle",
        "does not create production-quality PPTX output",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7H.1 renderer worker boundary contract preflight",
        "Python PresentationIR -> Node/PptxGenJS renderer input -> artifact/proof bundle",
        "self-contained apply-runner",
        "dirty tree already-applied diagnostic",
        "TARGETED PASS, LOCAL ACCEPT, and REMOTE ACCEPT boundaries",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7H.1 adds renderer worker boundary contract preflight",
        "without production PPTX renderer claims",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim KR-7H.1 renders production-quality PPTX",
        "claim artifact/proof bundle is produced by KR-7H.1",
        "start Node/PptxGenJS or LibreOffice runtime from KR-7H.1",
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
        "schema_version": "kw_renderer_worker_contract_check.v1",
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
        print(f"kw_renderer_worker_contract_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
