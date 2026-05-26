#!/usr/bin/env python3
"""Validate the KR-7C API-first Presentation contract surface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_API_V1_METHODS: dict[str, set[str]] = {
    "/api/v1/presentations": {"post"},
    "/api/v1/presentations/{presentation_id}": {"get"},
    "/api/v1/presentations/{presentation_id}/sources": {"get", "post"},
    "/api/v1/presentations/{presentation_id}/evidence": {"get"},
    "/api/v1/presentations/{presentation_id}/evidence/search": {"get"},
    "/api/v1/presentations/{presentation_id}/evidence/claims": {"get"},
    "/api/v1/presentations/{presentation_id}/plan": {"get", "post"},
    "/api/v1/presentations/{presentation_id}/ir": {"get"},
    "/api/v1/presentations/{presentation_id}/ir/versions": {"get"},
    "/api/v1/presentations/{presentation_id}/slides": {"get"},
    "/api/v1/presentations/{presentation_id}/slides/{slide_id}": {"patch"},
    "/api/v1/presentations/{presentation_id}/render": {"post"},
    "/api/v1/presentations/{presentation_id}/export": {"post"},
    "/api/v1/presentations/{presentation_id}/quality": {"get"},
}

LEGACY_COMPATIBILITY_METHODS: dict[str, set[str]] = {
    "/tasks": {"post"},
    "/tasks/{task_id}/execute": {"post"},
    "/presentations/{presentation_id}": {"get"},
    "/presentations/{presentation_id}/plan": {"get"},
}

REQUIRED_SCHEMA_NAMES = {
    "PresentationApiCreateRequestSchema",
    "PresentationApiSourceAttachRequestSchema",
    "PresentationApiSourceRefSchema",
    "PresentationApiSourcesResponseSchema",
    "PresentationEvidenceIndexResponseSchema",
    "PresentationEvidenceSearchResponseSchema",
    "PresentationEvidenceClaimAssessmentResponseSchema",
    "PresentationApiPlanRequestSchema",
    "PresentationApiSlidePatchRequestSchema",
    "PresentationApiRenderRequestSchema",
    "PresentationApiMetadataResponseSchema",
    "PresentationApiPlanSnapshotResponseSchema",
    "PresentationApiSlidesResponseSchema",
    "PresentationApiContractStatusSchema",
    "PresentationIRSnapshotResponseSchema",
    "PresentationIRVersionSummarySchema",
    "PresentationIRVersionsResponseSchema",
}

REQUIRED_PRESENTATION_IR_SOURCE_PHRASES = {
    "backend/app/services/slides_service/presentation_ir.py": (
        'PRESENTATION_IR_SCHEMA_VERSION = "presentation_ir.v1"',
        "def validate_presentation_ir_payload",
        "def build_presentation_ir_from_legacy_plan",
        "def detect_presentation_ir_storage_format",
    ),
    "backend/app/services/slides_service/plan_snapshot.py": (
        "def create_presentation_ir_snapshot",
        "def get_latest_presentation_ir",
        "def list_ir_snapshot_versions",
    ),
}

REQUIRED_SOURCE_ATTACHMENT_PHRASES = {
    "backend/app/services/slides_service/presentation_ir.py": (
        'PRESENTATION_IR_SOURCE_ATTACHMENT_CONTRACT_VERSION = "presentation_source_attachment.v1"',
        "def presentation_ir_source_attachments",
        "sources[{index}].{key} is required",
    ),
    "backend/app/api/routes/presentation_api_v1.py": (
        "def list_presentation_sources_v1",
        "extraction_runtime_implemented=False",
        "attachment_contract_version=PRESENTATION_IR_SOURCE_ATTACHMENT_CONTRACT_VERSION",
    ),
}


def build_report(repo_root: Path | None = None) -> dict[str, Any]:
    if repo_root is not None:
        root = str(repo_root)
        if root not in sys.path:
            sys.path.insert(0, root)
    from backend.app.main import app

    openapi = app.openapi()
    paths: dict[str, Any] = openapi.get("paths", {})
    schemas: dict[str, Any] = openapi.get("components", {}).get("schemas", {})
    tags = {item.get("name") for item in openapi.get("tags", []) if isinstance(item, dict)}

    missing_paths: list[dict[str, object]] = []
    missing_legacy_paths: list[dict[str, object]] = []
    missing_schemas = sorted(schema for schema in REQUIRED_SCHEMA_NAMES if schema not in schemas)

    for path, methods in REQUIRED_API_V1_METHODS.items():
        present_methods = set(paths.get(path, {}).keys())
        for method in methods:
            if method not in present_methods:
                missing_paths.append({"path": path, "method": method})

    for path, methods in LEGACY_COMPATIBILITY_METHODS.items():
        present_methods = set(paths.get(path, {}).keys())
        for method in methods:
            if method not in present_methods:
                missing_legacy_paths.append({"path": path, "method": method})

    missing_tags = [] if "presentation-api-v1" in tags else ["presentation-api-v1"]
    missing_ir_source_phrases: list[dict[str, str]] = []
    missing_source_attachment_phrases: list[dict[str, str]] = []
    if repo_root is not None:
        for relative_path, phrases in REQUIRED_PRESENTATION_IR_SOURCE_PHRASES.items():
            path = repo_root / relative_path
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            for phrase in phrases:
                if phrase not in text:
                    missing_ir_source_phrases.append({"path": relative_path, "required_phrase": phrase})
        for relative_path, phrases in REQUIRED_SOURCE_ATTACHMENT_PHRASES.items():
            path = repo_root / relative_path
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            for phrase in phrases:
                if phrase not in text:
                    missing_source_attachment_phrases.append({"path": relative_path, "required_phrase": phrase})
    issues: list[str] = []
    issues.extend(f"missing API v1 path/method: {entry['method'].upper()} {entry['path']}" for entry in missing_paths)
    issues.extend(
        f"missing legacy compatibility path/method: {entry['method'].upper()} {entry['path']}"
        for entry in missing_legacy_paths
    )
    issues.extend(f"missing OpenAPI schema: {schema}" for schema in missing_schemas)
    issues.extend(f"missing OpenAPI tag: {tag}" for tag in missing_tags)
    issues.extend(
        f"{entry['path']} missing PresentationIR source phrase: {entry['required_phrase']}"
        for entry in missing_ir_source_phrases
    )
    issues.extend(
        f"{entry['path']} missing Presentation source attachment phrase: {entry['required_phrase']}"
        for entry in missing_source_attachment_phrases
    )

    return {
        "schema_version": "kw_presentation_api_contract.v1",
        "status": "ready" if not issues else "not_ready",
        "required_api_v1_methods": {path: sorted(methods) for path, methods in REQUIRED_API_V1_METHODS.items()},
        "legacy_compatibility_methods": {path: sorted(methods) for path, methods in LEGACY_COMPATIBILITY_METHODS.items()},
        "missing_paths": missing_paths,
        "missing_legacy_paths": missing_legacy_paths,
        "missing_schemas": missing_schemas,
        "missing_tags": missing_tags,
        "missing_ir_source_phrases": missing_ir_source_phrases,
        "missing_source_attachment_phrases": missing_source_attachment_phrases,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless the contract is ready.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not (repo_root / "backend" / "app" / "main.py").exists():
        raise SystemExit(f"repo root does not look like KW Studio: {repo_root}")

    report = build_report(repo_root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Presentation API contract status: {report['status']}")
        for issue in report["issues"]:
            print(f"- {issue}")

    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
