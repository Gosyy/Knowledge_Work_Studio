from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.kw_repo_cleanup_audit import analyze_repository, write_report_outputs, make_zip


def test_repository_cleanup_audit_classifies_stage_docs_tests_and_portability(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "docs/codex").mkdir(parents=True)
    (repo / "docs/workflows").mkdir(parents=True)
    (repo / "backend/tests/smoke").mkdir(parents=True)
    (repo / "scripts").mkdir(parents=True)
    (repo / "backend/app/services").mkdir(parents=True)

    (repo / "docs/codex/S13_EXAMPLE.md").write_text("old stage doc\n", encoding="utf-8")
    (repo / "docs/workflows/DOCX_WORKFLOW.md").write_text("DOCX product workflow\n", encoding="utf-8")
    (repo / "backend/tests/smoke/test_s13_example.py").write_text("def test_example(): pass\n", encoding="utf-8")
    (repo / "scripts/kw_s13_example.py").write_text("print('stage script')\n", encoding="utf-8")
    (repo / "backend/app/services/path_example.py").write_text(
        "PROFILE_PATH = '/home/editor/workplace/Knowledge_Work_Studio'\n",
        encoding="utf-8",
    )

    report = analyze_repository(repo)

    assert report.summary["docs_archive_or_delete_candidates"] == 1
    assert report.summary["tests_rewrite_or_delete_candidates"] == 1
    assert report.summary["scripts_archive_or_replace_candidates"] == 1
    assert any(item.pattern == "absolute_home_path" for item in report.portability_findings)
    assert any(item.workflow == "xlsx" and item.status == "incomplete" for item in report.workflow_coverage)


def test_repository_cleanup_audit_writes_json_markdown_and_zip(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "docs/product").mkdir(parents=True)
    (repo / "docs/product/PRODUCT_VISION.md").write_text("KW Studio\n", encoding="utf-8")

    report = analyze_repository(repo)
    output_dir = tmp_path / "audit"
    written = write_report_outputs(report, output_dir)
    zip_path = make_zip(written, tmp_path / "audit.zip", base_dir=output_dir)

    assert (output_dir / "cleanup_inventory.json").exists()
    assert (output_dir / "cleanup_inventory.md").exists()
    payload = json.loads((output_dir / "cleanup_inventory.json").read_text(encoding="utf-8"))
    assert payload["summary"]["docs_total"] == 1

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
    assert "cleanup_inventory.json" in names
    assert "cleanup_inventory.md" in names
