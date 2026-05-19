from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_kr5a_xlsx_inspect_checker_is_ready(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_xlsx_inspect_workflow_check.py",
            "--repo-root",
            str(REPO_ROOT),
            "--output-dir",
            str(tmp_path),
            "--json",
            "--require-ready",
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["summary"]["workbook_opens"] is True
    assert payload["summary"]["formula_count"] == 1
    assert "table_previews/Revenue.csv" in payload["artifact_names"]
    assert (tmp_path / "kr5a_xlsx_inspect_bundle" / "quality_report.json").exists()


def test_kr5a_production_gate_includes_xlsx_inspect_guardrail() -> None:
    gate_text = (REPO_ROOT / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "KR-5A XLSX inspect workflow" in gate_text
    assert "scripts/kw_xlsx_inspect_workflow_check.py" in gate_text
