from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REQUIRED_CONTRACTS = {
    "api_contract",
    "docker_smoke",
    "gigachat_runtime",
    "production_readiness",
    "render_visual_qa",
    "slides_workflow",
    "source_mode_routing",
}


def _run_inventory(repo_root: Path, tmp_path: Path) -> dict[str, object]:
    script = repo_root / "scripts" / "kw_test_inventory.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--output-dir", str(tmp_path), "--require-ready"],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    inventory_path = tmp_path / "test_inventory.json"
    markdown_path = tmp_path / "test_inventory.md"
    assert inventory_path.exists(), completed.stdout + completed.stderr
    assert markdown_path.exists(), completed.stdout + completed.stderr
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    assert "KW Studio test portfolio inventory" in markdown_path.read_text(encoding="utf-8")
    assert "Duplicate / overlap clusters" in markdown_path.read_text(encoding="utf-8")
    return inventory


def test_kw_test_inventory_generates_contract_map(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    inventory = _run_inventory(repo_root, tmp_path)

    assert inventory["schema_version"] == "kw_test_inventory.v1"
    assert inventory["summary"]["total_files"] > 0
    assert inventory["summary"]["estimated_test_items"] > 0

    tests = inventory["tests"]
    all_contracts = {contract for entry in tests for contract in entry["contracts"]}
    assert REQUIRED_CONTRACTS <= all_contracts
    assert REQUIRED_CONTRACTS <= set(inventory["summary"]["contract_membership"])
    assert REQUIRED_CONTRACTS <= set(inventory["summary"]["by_contract_membership"])
    assert "source_mode_routing" in inventory["summary"]["by_contract_membership"]
    # Some cross-cutting contracts are intentionally secondary. The primary
    # distribution remains available as by_contract/by_primary_contract, while
    # coverage/readiness checks must use membership.
    assert inventory["summary"]["by_contract"] == inventory["summary"]["by_primary_contract"]

    decisions = {entry["decision"] for entry in tests}
    assert "delete" not in decisions
    assert decisions <= {"keep", "merge", "quarantine", "rewrite"}


def test_kw_test_inventory_classifies_slides_workflow_by_path(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    inventory = _run_inventory(repo_root, tmp_path)
    by_path = {entry["path"]: entry for entry in inventory["tests"]}

    slides_routing = by_path["backend/tests/workflows/test_slides_source_mode_routing.py"]
    assert slides_routing["contract"] == "slides_workflow"
    assert "source_mode_routing" in slides_routing["contracts"]

    rf2_closure = by_path["backend/tests/smoke/test_rf2_closure_slides_runtime.py"]
    assert rf2_closure["contract"] == "slides_workflow"
    assert "render_visual_qa" in rf2_closure["contracts"] or "production_readiness" in rf2_closure["contracts"]


def test_kw_test_inventory_preserves_acceptance_runners(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    inventory = _run_inventory(repo_root, tmp_path)
    by_path = {entry["path"]: entry for entry in inventory["tests"]}

    full_runner = by_path["scripts/kw_product_full_runner_logged.sh"]
    docker_smoke = by_path["scripts/kw_product_docker_smoke_logged.sh"]
    assert full_runner["tier"] == "tier5_full_runner"
    assert full_runner["contract"] == "production_readiness"
    assert full_runner["decision"] == "keep"
    assert docker_smoke["tier"] == "tier6_docker_smoke"
    assert docker_smoke["contract"] == "docker_smoke"
    assert docker_smoke["decision"] == "keep"
