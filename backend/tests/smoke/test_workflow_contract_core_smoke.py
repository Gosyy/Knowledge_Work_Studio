from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_kr4a_workflow_contract_core_cli_ready() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_workflow_contract_core_check.py",
            "--repo-root",
            str(REPO_ROOT),
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
    assert payload["workflow_count"] == 6
    assert set(payload["mandatory_product_workflow_ids"]) == {
        "docx",
        "pdf",
        "xlsx",
        "slides",
        "python_analysis",
        "browser_evidence",
    }


def test_kr4a_workflow_contract_core_cli_filters_xlsx() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_workflow_contract_core_check.py",
            "--repo-root",
            str(REPO_ROOT),
            "--workflow",
            "xlsx",
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
    assert payload["workflow_count"] == 1
    assert set(payload["contracts"]) == {"xlsx"}
    assert "formula_inventory.json" in {artifact["name"] for artifact in payload["contracts"]["xlsx"]["artifacts"]}


def test_kr4a_production_gate_includes_workflow_contract_core() -> None:
    gate_text = (REPO_ROOT / "scripts" / "kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "Workflow contract core" in gate_text
    assert "scripts/kw_workflow_contract_core_check.py" in gate_text
    assert "docs/architecture/WORKFLOW_CONTRACT_CORE.md" in gate_text
