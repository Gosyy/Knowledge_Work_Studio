#!/usr/bin/env python3
"""Validate the KR-5A XLSX inspect workflow runtime and artifact bundle."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_ARTIFACTS = {
    "workbook.xlsx",
    "workbook_manifest.json",
    "xlsx_analysis_report.json",
    "formula_inventory.json",
    "table_previews/Revenue.csv",
    "source_evidence_manifest.json",
    "artifact_manifest.json",
    "quality_report.json",
}

REQUIRED_PROJECT_FILES = (
    "backend/app/services/xlsx_service/__init__.py",
    "backend/app/services/xlsx_service/inspector.py",
    "backend/app/services/xlsx_service/service.py",
    "backend/app/services/xlsx_service/entrypoint.py",
    "docs/workflows/XLSX_WORKFLOW.md",
    "docs/quality/XLSX_VALIDATION.md",
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md",
)


def ensure_repo_on_path(repo_root: Path) -> None:
    repo_text = str(repo_root)
    if repo_text not in sys.path:
        sys.path.insert(0, repo_text)


def _json_load(payload: bytes) -> dict[str, Any]:
    return json.loads(payload.decode("utf-8"))


def build_report(repo_root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    ensure_repo_on_path(repo_root)

    from backend.app.services.xlsx_service import XlsxService, sample_xlsx_bytes

    service = XlsxService()
    sample = sample_xlsx_bytes()
    bundle = service.build_artifact_bundle(sample, source_filename="revenue_sample.xlsx")
    result = bundle.result
    artifact_names = set(bundle.artifact_names())

    written_artifacts: list[str] = []
    if output_dir is not None:
        written_artifacts = service.write_artifact_bundle(
            sample,
            output_dir=output_dir / "kr5a_xlsx_inspect_bundle",
            source_filename="revenue_sample.xlsx",
        )

    missing_project_files = [path for path in REQUIRED_PROJECT_FILES if not (repo_root / path).exists()]
    missing_artifacts = sorted(REQUIRED_ARTIFACTS - artifact_names)

    quality = _json_load(bundle.artifacts["quality_report.json"])
    manifest = _json_load(bundle.artifacts["artifact_manifest.json"])
    formula_inventory = _json_load(bundle.artifacts["formula_inventory.json"])
    workbook_manifest = _json_load(bundle.artifacts["workbook_manifest.json"])
    analysis = _json_load(bundle.artifacts["xlsx_analysis_report.json"])

    issues: list[str] = []
    issues.extend(f"missing project file: {path}" for path in missing_project_files)
    issues.extend(f"missing bundle artifact: {path}" for path in missing_artifacts)
    if result.status != "ready":
        issues.append(f"sample workbook inspection status is {result.status}: {result.errors}")
    if not result.workbook_opens:
        issues.append("sample workbook did not open")
    if result.sheet_count < 1:
        issues.append("sheet metadata was not extracted")
    if result.formula_count < 1:
        issues.append("formula inventory is empty")
    if result.table_like_row_count < 1:
        issues.append("table-like rows were not detected")
    if result.destructive_edit_performed:
        issues.append("XLSX inspect workflow reported destructive edit")
    if quality.get("status") != "ready":
        issues.append("quality_report.json is not ready")
    if not quality.get("checks", {}).get("table_previews_written"):
        issues.append("quality report does not confirm table preview output")
    if formula_inventory.get("formula_count", 0) < 1:
        issues.append("formula_inventory.json does not record formulas")
    if workbook_manifest.get("sheet_count", 0) < 1:
        issues.append("workbook_manifest.json does not record sheet metadata")
    if analysis.get("source_kind") != "xlsx":
        issues.append("xlsx_analysis_report.json does not record source_kind=xlsx")
    manifest_paths = {item.get("path") for item in manifest.get("artifacts", [])}
    if not REQUIRED_ARTIFACTS.issubset(manifest_paths):
        issues.append("artifact_manifest.json does not list all required KR-5A artifacts")

    return {
        "status": "ready" if not issues else "not_ready",
        "schema_version": result.schema_version,
        "workflow_id": "xlsx",
        "repo_root": str(repo_root),
        "required_project_files": list(REQUIRED_PROJECT_FILES),
        "missing_project_files": missing_project_files,
        "required_artifacts": sorted(REQUIRED_ARTIFACTS),
        "artifact_names": sorted(artifact_names),
        "missing_artifacts": missing_artifacts,
        "written_artifacts": written_artifacts,
        "summary": {
            "workbook_opens": result.workbook_opens,
            "sheet_count": result.sheet_count,
            "formula_count": result.formula_count,
            "table_like_row_count": result.table_like_row_count,
            "non_empty_cell_count": result.non_empty_cell_count,
            "destructive_edit_performed": result.destructive_edit_performed,
            "source_sha256_recorded": bool(result.source_sha256),
        },
        "quality_report_status": quality.get("status"),
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory for a sample KR-5A bundle.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless the report is ready.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    report = build_report(repo_root, output_dir)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KR-5A XLSX inspect workflow status: {report['status']}")
        for issue in report["issues"]:
            print(f"- {issue}")

    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
