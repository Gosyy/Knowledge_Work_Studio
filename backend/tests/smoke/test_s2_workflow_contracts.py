from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from backend.app.workflows.contracts import (
    REQUIRED_WORKFLOW_IDS,
    get_workflow_contract,
    validate_workflow_contracts,
    workflow_contract_report,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHON = os.environ.get("KW_TEST_PYTHON", sys.executable)


def run_contract_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "scripts/kw_workflow_contracts_check.py", "--repo-root", str(REPO_ROOT), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_s2_required_workflow_contracts_are_present_and_ready() -> None:
    report = workflow_contract_report()

    assert report["status"] == "ready"
    assert set(report["contracts"]) == set(REQUIRED_WORKFLOW_IDS)
    assert validate_workflow_contracts() == []


def test_s2_slides_contract_is_outline_first_and_plan_snapshot_based() -> None:
    slides = get_workflow_contract("slides")

    assert slides.user_visible is True
    assert "outline_first_plan" in slides.lifecycle
    assert "editable_plan_before_generation" in slides.approval_gates
    assert "retry_from_saved_plan" in slides.approval_gates
    assert "plan_snapshot" in slides.output_artifact_kinds
    assert slides.provenance_required is True


def test_s2_browser_contract_remains_internal_only() -> None:
    browser = get_workflow_contract("browser_assisted")

    assert browser.user_visible is False
    assert browser.browser_policy == "internal_only"
    assert "explicit_internal_navigation_approval" in browser.approval_gates
    assert browser.offline_ready is True


def test_s2_llm_contract_keeps_gigachat_as_default_provider_gate() -> None:
    llm = get_workflow_contract("llm_provider")

    assert llm.user_visible is False
    assert "offline_provider_must_be_gigachat_by_default" in llm.approval_gates
    assert any("GigaChat" in note for note in llm.notes)


def test_s2_workflow_contract_cli_outputs_json() -> None:
    result = run_contract_check("--json", "--require-ready")

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["workflow_count"] == len(REQUIRED_WORKFLOW_IDS)
    assert "docx" in payload["contracts"]


def test_s2_workflow_contract_cli_filters_single_workflow() -> None:
    result = run_contract_check("--workflow", "slides", "--json", "--require-ready")

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["workflow_count"] == 1
    assert set(payload["contracts"]) == {"slides"}


def test_s2_workflow_contract_cli_rejects_unknown_workflow() -> None:
    result = run_contract_check("--workflow", "unknown", "--require-ready")

    assert result.returncode == 1
    assert "unknown workflow contract: unknown" in result.stdout


def test_s2_production_gate_includes_workflow_contract_step() -> None:
    gate_text = (REPO_ROOT / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "scripts/kw_workflow_contracts_check.py" in gate_text
    assert "Workflow contracts registry" in gate_text
    assert "docs/workflow-contracts.md" in gate_text
