from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_kr5b_xlsx_validation_bundle_checker_ready(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_xlsx_validation_bundle_check.py",
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
    assert payload["validation"]["status"] == "ready"
    assert payload["validation"]["checks"]["manifest_hashes_match"] is True
    assert (tmp_path / "kr5b_xlsx_validated_bundle" / "bundle_validation_report.json").exists()


def test_kr5b_production_gate_includes_xlsx_validation_bundle_guardrail() -> None:
    gate_text = (REPO_ROOT / "scripts" / "kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "KR-5B XLSX validation bundle" in gate_text
    assert "scripts/kw_xlsx_validation_bundle_check.py" in gate_text
