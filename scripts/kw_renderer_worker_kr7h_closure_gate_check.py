#!/usr/bin/env python3
"""KR-7H.13 renderer worker closure gate checker.

This checker closes the KR-7H renderer-worker foundation phase only. It verifies
that KR-7H.1 through KR-7H.12 contracts are present and still fail closed where
production renderer, visual QA, Kimi-level quality, source image selection, or
professional layout claims would be premature.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.services.slides_service import (  # noqa: E402
    RENDERER_WORKER_KR7H_CLOSURE_GATE_SCHEMA_VERSION,
    renderer_worker_kr7h_closure_gate_payload,
)

REQUIRED_LAYER_PHASES = [
    "KR-7H.1",
    "KR-7H.2",
    "KR-7H.3",
    "KR-7H.4",
    "KR-7H.5",
    "KR-7H.6",
    "KR-7H.7",
    "KR-7H.8",
    "KR-7H.9",
    "KR-7H.10",
    "KR-7H.11",
    "KR-7H.12",
]

REQUIRED_FILES = [
    "backend/tests/services/test_kr7h_renderer_worker_kr7h_closure_gate.py",
    "scripts/kw_renderer_worker_kr7h_closure_gate_check.py",
    "scripts/kw_renderer_worker_contract_check.py",
    "scripts/kw_renderer_worker_dry_run_check.py",
    "scripts/kw_renderer_worker_protocol_check.py",
    "scripts/kw_renderer_worker_package_check.py",
    "scripts/kw_renderer_worker_pptxgenjs_capability_check.py",
    "scripts/kw_renderer_worker_pptxgenjs_in_memory_check.py",
    "scripts/kw_renderer_worker_empty_pptx_output_check.py",
    "scripts/kw_renderer_worker_static_slide_output_check.py",
    "scripts/kw_renderer_worker_minimal_ir_mapping_check.py",
    "scripts/kw_renderer_worker_pptx_artifact_bundle_check.py",
    "scripts/kw_renderer_worker_libreoffice_proof_bundle_check.py",
    "scripts/kw_renderer_worker_source_image_hardening_check.py",
]

FULL_RUNNER_STEPS = [
    "29h-renderer-worker-contract-check",
    "29h2-renderer-worker-dry-run-check",
    "29h3-renderer-worker-protocol-check",
    "29h4-renderer-worker-package-check",
    "29h5-renderer-worker-pptxgenjs-capability-check",
    "29h6-renderer-worker-pptxgenjs-in-memory-check",
    "29h7-renderer-worker-empty-pptx-output-check",
    "29h8-renderer-worker-static-slide-output-check",
    "29h9-renderer-worker-minimal-ir-mapping-check",
    "29h10-renderer-worker-pptx-artifact-bundle-check",
    "29h11-renderer-worker-libreoffice-proof-bundle-check",
    "29h12-renderer-worker-source-image-hardening-check",
    "29h13-renderer-worker-kr7h-closure-gate-check",
]

PACKAGE_EXPECTED = {
    "kr7h_closure_gate_schema_version": RENDERER_WORKER_KR7H_CLOSURE_GATE_SCHEMA_VERSION,
    "kr7h_closure_gate_implemented": True,
    "kr7h_phase_closed": True,
    "closed_through_phase": "KR-7H.13",
    "production_renderer_closure_implemented": False,
    "renderer_runtime_implemented": False,
    "production_pptx_output_implemented": False,
    "visual_qa_executed": False,
    "visual_quality_score": None,
    "kimi_level_quality_claimed": False,
    "source_image_selection_implemented": False,
    "image_mapping_implemented": False,
    "fake_artifacts_allowed": False,
    "fallback_renderer_allowed": False,
}

REQUIRED_DOC_PHRASES = {
    "renderer_worker/CONTRACT.md": [
        "KR-7H.13 closure gate",
        "presentation_renderer_worker_kr7h_closure_gate.v1",
        "production_renderer_closure_implemented=false",
        "kimi_level_quality_claimed=false",
        "KR-7I template and brand understanding",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "KR-7H.13 KR-7H closure gate",
        "presentation_renderer_worker_kr7h_closure_gate.v1",
        "KR-7I template and brand understanding",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7H.13",
        "KR-7H closure gate",
        "KR-7I template and brand understanding",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7H.13",
        "presentation_renderer_worker_kr7h_closure_gate.v1",
        "KR-7I template and brand understanding",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "KR-7H.13 renderer worker closure gate prohibitions",
        "claim KR-7H.13 closes the production renderer",
        "claim KR-7H.13 reaches Kimi-level quality",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7H.13 adds the KR-7H closure gate",
        "presentation_renderer_worker_kr7h_closure_gate.v1",
    ],
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _load_json(path: Path) -> Any:
    return json.loads(_read(path))


def _validate_payload(problems: list[str]) -> dict[str, Any]:
    payload = renderer_worker_kr7h_closure_gate_payload()
    expected = {
        "schema_version": RENDERER_WORKER_KR7H_CLOSURE_GATE_SCHEMA_VERSION,
        "status": "ready",
        "kr7h_closure_gate_implemented": True,
        "kr7h_phase_closed": True,
        "closed_through_phase": "KR-7H.13",
        "completed_layer_count": len(REQUIRED_LAYER_PHASES),
        "renderer_runtime_implemented": False,
        "production_pptx_output_implemented": False,
        "production_renderer_closure_implemented": False,
        "visual_qa_executed": False,
        "visual_quality_score": None,
        "source_image_selection_implemented": False,
        "image_mapping_implemented": False,
        "chart_mapping_implemented": False,
        "table_mapping_implemented": False,
        "theme_mapping_implemented": False,
        "professional_layout_engine_implemented": False,
        "kimi_level_quality_claimed": False,
        "fake_artifacts_allowed": False,
        "fallback_renderer_allowed": False,
        "next_phase": "KR-7I template and brand understanding",
    }
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value:
            problems.append(f"closure payload {key} expected {expected_value!r}, got {payload.get(key)!r}")
    phases = [layer.get("phase") for layer in payload.get("completed_layers", []) if isinstance(layer, dict)]
    if phases != REQUIRED_LAYER_PHASES:
        problems.append(f"closure payload completed_layers expected {REQUIRED_LAYER_PHASES!r}, got {phases!r}")
    non_goals = payload.get("non_goals") if isinstance(payload.get("non_goals"), list) else []
    for non_goal in (
        "no_production_renderer_closure",
        "no_visual_qa_scoring",
        "no_kimi_level_quality_claim",
        "no_source_image_selection_runtime",
        "no_image_mapping_runtime",
        "no_frontend_changes",
        "no_gigachat_runtime_changes",
    ):
        if non_goal not in non_goals:
            problems.append(f"closure payload non_goals missing {non_goal}")
    return payload


def _validate_files(repo_root: Path, problems: list[str]) -> None:
    missing = [path for path in REQUIRED_FILES if not (repo_root / path).is_file()]
    for path in missing:
        problems.append(f"required KR-7H closure file missing: {path}")


def _validate_package(repo_root: Path, problems: list[str]) -> None:
    try:
        package = _load_json(repo_root / "renderer_worker" / "package.json")
    except Exception as exc:  # noqa: BLE001
        problems.append(f"renderer_worker/package.json is not valid JSON: {exc}")
        return
    metadata = package.get("kwStudio") if isinstance(package, dict) else None
    if not isinstance(metadata, dict):
        problems.append("renderer_worker/package.json kwStudio metadata must be an object")
        return
    for key, expected in PACKAGE_EXPECTED.items():
        if metadata.get(key) != expected:
            problems.append(f"renderer_worker kwStudio.{key} expected {expected!r}, got {metadata.get(key)!r}")
    phases = metadata.get("kr7h_completed_phases")
    if phases != REQUIRED_LAYER_PHASES + ["KR-7H.13"]:
        problems.append("renderer_worker kwStudio.kr7h_completed_phases must list KR-7H.1 through KR-7H.13")
    for non_goal in ("no_production_renderer_closure", "no_kimi_level_quality_claim", "no_visual_qa_scoring"):
        if non_goal not in metadata.get("non_goals", []):
            problems.append(f"renderer_worker kwStudio.non_goals missing {non_goal}")


def _validate_full_runner(repo_root: Path, problems: list[str]) -> None:
    text = _read(repo_root / "scripts" / "kw_full_tests_with_proxy_runner.sh")
    for step in FULL_RUNNER_STEPS:
        if step not in text:
            problems.append(f"full runner missing renderer worker closure sequence step: {step}")
    if "kw_renderer_worker_kr7h_closure_gate_check.py --repo-root . --require-ready" not in text:
        problems.append("full runner must execute kw_renderer_worker_kr7h_closure_gate_check.py --repo-root . --require-ready")


def _validate_docs(repo_root: Path, problems: list[str]) -> None:
    for relative_path, phrases in REQUIRED_DOC_PHRASES.items():
        path = repo_root / relative_path
        if not path.is_file():
            problems.append(f"documentation file missing for KR-7H.13 closure gate: {relative_path}")
            continue
        text = _read(path)
        for phrase in phrases:
            if phrase not in text:
                problems.append(f"{relative_path} missing required KR-7H.13 phrase: {phrase}")


def build_report(repo_root: Path) -> dict[str, Any]:
    problems: list[str] = []
    payload = _validate_payload(problems)
    _validate_files(repo_root, problems)
    _validate_package(repo_root, problems)
    _validate_full_runner(repo_root, problems)
    _validate_docs(repo_root, problems)
    return {
        "schema_version": RENDERER_WORKER_KR7H_CLOSURE_GATE_SCHEMA_VERSION,
        "status": "ready" if not problems else "blocked",
        "closure_payload": payload,
        "checked_layer_count": len(REQUIRED_LAYER_PHASES),
        "required_full_runner_step": "29h13-renderer-worker-kr7h-closure-gate-check",
        "problems": problems,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    report = build_report(args.repo_root.resolve())
    print(f"kw_renderer_worker_kr7h_closure_gate_check.py: {report['status']}")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
