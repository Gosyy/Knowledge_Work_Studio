from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "kw_s3_adaptive_deck_modes_check.py"


def run_checker(*extra: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(REPO_ROOT), "--json", *extra],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


def test_s3_adaptive_deck_modes_ready() -> None:
    payload = run_checker()
    assert payload["status"] == "ready"
    assert payload["adaptive_deck_modes_completed_by_s3"] is True
    assert payload["adaptive_deck_mode_count"] == 5
    assert payload["slide_archetype_registry_ready_by_s3"] is True


def test_s3_includes_core_benchmark_modes() -> None:
    payload = run_checker()
    modes = set(payload["adaptive_deck_mode_ids"])
    assert "executive_board_deck" in modes
    assert "architecture_review_deck" in modes
    assert "project_status_deck" in modes
    assert "decision_matrix_deck" in modes
    assert "long_document_explainer" in modes


def test_s3_preserves_offline_and_release_boundaries() -> None:
    payload = run_checker()
    assert payload["offline_ready_by_s3"] is True
    assert payload["public_internet_required_by_s3"] is False
    assert payload["browser_runtime_required_by_s3"] is False
    assert payload["api_endpoint_added_by_s3"] is False
    assert payload["db_schema_migration_added_by_s3"] is False
    assert payload["dependency_versions_changed_by_s3"] is False
    assert payload["kimi_level_claimed_by_s3"] is False
    assert payload["server3_local_intranet_route_verified_by_s3"] is False


def test_s3_prepares_s4_and_s9() -> None:
    payload = run_checker()
    assert payload["table_chart_policy_ready_for_s4"] is True
    assert payload["visual_qa_expectations_ready_for_s9"] is True
    assert payload["source_to_slide_provenance_required_by_s3"] is True
    assert payload["next_recommended_step"].startswith("S4")
