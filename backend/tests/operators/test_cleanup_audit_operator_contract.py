from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from scripts.kw_repo_cleanup_audit import analyze_repository, make_zip, report_to_dict, write_report_outputs


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_cleanup_audit_is_read_only_and_reports_required_product_workflows() -> None:
    report = analyze_repository(REPO_ROOT)
    payload = report_to_dict(report)

    assert payload["summary"]["workflow_count"] == 6
    assert payload["summary"]["workflow_incomplete_count"] == 0
    workflows = {item["workflow"]: item["status"] for item in payload["workflow_coverage"]}
    assert workflows["xlsx"] == "ready"
    assert workflows["docx"] == "ready"
    assert workflows["pdf"] == "ready"
    assert workflows["slides"] == "ready"


def test_cleanup_audit_writes_machine_readable_report_bundle(tmp_path: Path) -> None:
    report = analyze_repository(REPO_ROOT)
    output_dir = tmp_path / "audit"
    files = write_report_outputs(report, output_dir)

    expected = {
        "cleanup_inventory.json",
        "docs_inventory.json",
        "test_inventory.json",
        "scripts_inventory.json",
        "path_portability_findings.json",
        "workflow_coverage.json",
        "cleanup_inventory.md",
    }
    assert expected.issubset({path.name for path in files})

    zip_path = tmp_path / "audit.zip"
    make_zip(files, zip_path, base_dir=output_dir)
    with ZipFile(zip_path, "r") as archive:
        names = set(archive.namelist())

    assert expected.issubset(names)
