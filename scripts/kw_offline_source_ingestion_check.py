#!/usr/bin/env python3
"""Validate KR-7D offline source ingestion engine guardrails."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "backend/app/services/slides_service/offline_source_ingestion.py",
    "backend/app/services/slides_service/source_asset_registry.py",
    "backend/tests/services/test_kr7d_offline_source_ingestion.py",
]

REQUIRED_PHRASES = {
    "backend/app/services/slides_service/offline_source_ingestion.py": [
        'SOURCE_INGESTION_SCHEMA_VERSION = "offline_source_ingestion.v1"',
        'SOURCE_ASSET_REGISTRY_SCHEMA_VERSION = "source_asset_registry.v1"',
        "class OfflineSourceIngestionEngine",
        "def ingest_bytes",
        "def _ingest_docx",
        "def _ingest_pptx",
        "def _ingest_xlsx",
        "def _ingest_pdf",
        "does not fake PDF text or OCR",
        "provenance_manifest",
        "source_asset_registry",
        'SOURCE_STRUCTURE_SCHEMA_VERSION = "source_structure.v1"',
        "class SourceStructureElement",
        "class SourceChartDataCandidate",
        "def _markdown_structures",
        "def _docx_structures",
        "def _pptx_chart_candidates",
        "def _xlsx_chart_candidates",
        "def _pdf_page_structures",
    ],
    "backend/app/services/slides_service/source_asset_registry.py": [
        'SOURCE_ASSET_STORAGE_SCHEMA_VERSION = "source_asset_storage.v1"',
        "class SourceAssetRegistryStore",
        "def persist_report",
        "source-asset://",
        "relative_path",
        "never the operator's absolute storage root",
    ],
    "backend/tests/services/test_kr7d_offline_source_ingestion.py": [
        "test_kr7d_markdown_ingestion_extracts_headings_tables_and_provenance",
        "test_kr7d_docx_ingestion_extracts_paragraph_table_and_image_asset",
        "test_kr7d_pptx_ingestion_extracts_slide_text_and_media_assets",
        "test_kr7d_xlsx_ingestion_extracts_table_preview_and_formula_flag",
        "test_kr7d_pdf_without_runtime_dependency_reports_unsupported_not_fake_success",
        "test_kr7d_source_asset_registry_persists_extracted_asset_bytes",
        "test_kr7d_source_asset_registry_empty_report_is_honest",
        "test_kr7d_markdown_ingestion_extracts_code_blocks_and_image_refs",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7D.1 Offline source ingestion engine foundation",
        "DOCX, PPTX, XLSX/CSV, Markdown/text",
        "PDF extraction remains honest and dependency-gated",
        "KR-7D.2 SourceAssetRegistry persistence and extracted asset storage contract",
        "KR-7D.3 Richer document structure extraction",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7D.1 Offline source ingestion engine foundation",
        "does not implement OCR, embeddings, evidence retrieval, or PresentationIR planning",
        "KR-7D.2 SourceAssetRegistry persistence and extracted asset storage contract",
        "KR-7D.3 Richer document structure extraction",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7D.1 adds offline source ingestion foundation",
        "KR-7D.2 adds SourceAssetRegistry persistence",
        "KR-7D.3 enriches document structure extraction",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim PDF/OCR extraction readiness when the extractor returned unsupported",
        "expose operator absolute storage paths in SourceAssetRegistry manifests",
        "claim KR-7E evidence retrieval from KR-7D.3 structure metadata",
    ],
}


def build_report(repo_root: Path) -> dict[str, Any]:
    missing_files = [path for path in REQUIRED_FILES if not (repo_root / path).is_file()]
    missing_phrases: list[dict[str, str]] = []
    for relative_path, phrases in REQUIRED_PHRASES.items():
        path = repo_root / relative_path
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for phrase in phrases:
            if phrase not in text:
                missing_phrases.append({"path": relative_path, "required_phrase": phrase})
    issues = [f"missing required file: {path}" for path in missing_files]
    issues.extend(
        f"{entry['path']} missing KR-7D source ingestion phrase: {entry['required_phrase']}"
        for entry in missing_phrases
    )
    return {
        "schema_version": "kw_offline_source_ingestion_check.v1",
        "status": "ready" if not issues else "blocked",
        "missing_files": missing_files,
        "missing_phrases": missing_phrases,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    report = build_report(Path(args.repo_root).resolve())
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        for issue in report["issues"]:
            print(f"- {issue}")
    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
