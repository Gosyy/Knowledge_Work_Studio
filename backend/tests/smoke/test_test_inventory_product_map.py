from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[3] / "scripts" / "kw_test_inventory_product_map.py"
spec = importlib.util.spec_from_file_location("kw_test_inventory_product_map", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _write_audit_zip(path: Path) -> None:
    tests = [
        {"path": "backend/tests/api/test_artifact_download.py", "recommendation": "keep_or_consolidate", "reason": "api"},
        {"path": "backend/tests/smoke/test_kq1c_independent_render_qa.py", "recommendation": "rewrite_or_delete", "reason": "stage"},
        {"path": "backend/tests/smoke/test_s13j_executive_memo_salvage.py", "recommendation": "rewrite_or_delete", "reason": "stage"},
        {"path": "backend/tests/smoke/test_repository_cleanup_audit.py", "recommendation": "keep", "reason": "cleanup"},
    ]
    scripts = [
        {"path": "scripts/kw_production_readiness_gate.py", "recommendation": "keep", "reason": "gate"},
        {"path": "scripts/kw_kq1c_exec_memo_render_qa.py", "recommendation": "archive_or_replace", "reason": "stage"},
    ]
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("test_inventory.json", json.dumps(tests))
        zf.writestr("scripts_inventory.json", json.dumps(scripts))
        zf.writestr("path_portability_findings.json", "[]")
        zf.writestr("workflow_coverage.json", "[]")
        zf.writestr("cleanup_inventory.json", "{}")


def test_kr2a_report_classifies_stage_tests_and_product_targets(tmp_path: Path) -> None:
    audit_zip = tmp_path / "audit.zip"
    _write_audit_zip(audit_zip)

    audit = module.load_audit_zip(audit_zip)
    report = module.build_report(audit)

    assert report["status"] == "ready"
    assert report["summary"]["tests_total"] == 4
    assert report["summary"]["stage_tests_rewrite_or_archive_count"] == 2
    assert report["summary"]["stage_scripts_rewrite_or_archive_count"] == 1
    blockers = {item["path"]: item for item in report["physical_archive_blockers"]}
    assert blockers["backend/tests/smoke/test_kq1c_independent_render_qa.py"]["rewrite_target"] == "backend/tests/quality/test_pptx_render_qa.py"
    assert any(row["path"] == "backend/tests/workflows/test_xlsx_workflow.py" for row in report["product_test_target_status"])


def test_kr2a_cli_writes_json_markdown_and_zip(tmp_path: Path) -> None:
    audit_zip = tmp_path / "audit.zip"
    out_dir = tmp_path / "out"
    report_zip = tmp_path / "report.zip"
    _write_audit_zip(audit_zip)

    exit_code = module.main.__wrapped__() if hasattr(module.main, "__wrapped__") else None
    assert exit_code is None

    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "--audit-zip",
            str(audit_zip),
            "--output-dir",
            str(out_dir),
            "--zip-out",
            str(report_zip),
            "--require-ready",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (out_dir / "kr2a_test_inventory_product_map.json").exists()
    assert (out_dir / "kr2a_test_inventory_product_map.md").exists()
    assert report_zip.exists()
    with zipfile.ZipFile(report_zip, "r") as zf:
        assert "kr2a_test_inventory_product_map.json" in zf.namelist()
        assert "kr2a_product_test_targets.json" in zf.namelist()
