#!/usr/bin/env python3
"""Validate KR-5B XLSX validation and artifact bundle hardening."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_PROJECT_FILES = (
    "backend/app/services/xlsx_service/validator.py",
    "scripts/kw_xlsx_validation_bundle_check.py",
    "backend/tests/quality/test_xlsx_validation_bundle_hardening.py",
    "backend/tests/smoke/test_xlsx_validation_bundle_check.py",
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md",
)


def ensure_repo_on_path(repo_root: Path) -> None:
    repo_text = str(repo_root)
    if repo_text not in sys.path:
        sys.path.insert(0, repo_text)


def build_report(repo_root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    ensure_repo_on_path(repo_root)

    from backend.app.services.xlsx_service import XlsxService, sample_xlsx_bytes
    from backend.app.services.xlsx_service.validator import validate_xlsx_artifact_bundle

    missing_project_files = [path for path in REQUIRED_PROJECT_FILES if not (repo_root / path).exists()]
    service = XlsxService()
    bundle = service.build_artifact_bundle(sample_xlsx_bytes(), source_filename="revenue_sample.xlsx")
    validation = validate_xlsx_artifact_bundle(bundle)

    written_artifacts: list[str] = []
    if output_dir is not None:
        bundle_dir = output_dir / "kr5b_xlsx_validated_bundle"
        written_artifacts = service.write_artifact_bundle(
            sample_xlsx_bytes(),
            output_dir=bundle_dir,
            source_filename="revenue_sample.xlsx",
        )
        (bundle_dir / "bundle_validation_report.json").write_text(
            json.dumps(validation.as_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written_artifacts.append("bundle_validation_report.json")

    issues = list(validation.as_dict()["issues"])
    for path in missing_project_files:
        issues.append({"code": "missing_project_file", "message": f"missing project file: {path}", "artifact": path})

    return {
        "status": "ready" if validation.status == "ready" and not missing_project_files else "not_ready",
        "workflow_id": "xlsx",
        "schema_version": validation.schema_version,
        "repo_root": str(repo_root),
        "validation": validation.as_dict(),
        "artifact_names": sorted(bundle.artifact_names()),
        "written_artifacts": sorted(written_artifacts),
        "missing_project_files": missing_project_files,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--output-dir", default=None, help="Optional output dir for validation sample bundle.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless report is ready.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(Path(args.repo_root).expanduser().resolve(), output_dir)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KR-5B XLSX validation bundle status: {report['status']}")
        for issue in report["issues"]:
            print(f"- {issue}")
    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
