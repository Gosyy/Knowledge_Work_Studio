from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "kw_s1_kimi_slides_gap_check.py"


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


@pytest.fixture(scope="module")
def s1_report() -> dict:
    return run_checker()


def test_s1_opens_all_ten_s_phases(s1_report: dict) -> None:
    report = s1_report
    assert report["status"] == "ready"
    assert report["s_phase_track_opened_by_s1"] is True
    assert report["s_phase_count"] == 10
    assert report["s_phase_ids"] == ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"]
    assert report["first_execution_phase_after_s1"] == "S2"


def test_s1_records_required_capability_gaps(s1_report: dict) -> None:
    report = s1_report
    expected = {
        "outline_first_workflow",
        "editable_plan_before_generation",
        "adaptive_deck_modes",
        "native_table_chart_diagram_rendering",
        "template_master_ingestion",
        "image_screenshot_to_slide_workflow",
        "offline_research_citations",
        "conversational_edit_loop",
        "render_based_visual_qa",
        "expanded_kimi_style_benchmark",
    }
    assert set(report["capability_gap_ids"]) == expected
    assert report["capability_gap_count"] == 10
    assert len(report["capability_gap_matrix"]) == 10


def test_s1_preserves_no_kimi_or_server3_claims(s1_report: dict) -> None:
    report = s1_report
    assert report["kimi_slides_class_goal_declared"] is True
    assert report["kimi_level_claimed_by_s1"] is False
    assert report["whole_project_kimi_level_supported"] is False
    assert report["kimi_slides_class_parity_claim_supported_by_s1"] is False
    assert report["offline_intranet_constraint_preserved_by_s1"] is True
    assert report["server3_local_intranet_route_verified_by_s1"] is False
    assert report["public_api_dev_gigachat_evidence_remains_completion_evidence_not_server3_proof"] is True


def test_s1_report_has_digest_and_next_step(s1_report: dict) -> None:
    report = s1_report
    assert report["s1_gap_dossier_digest"].startswith("sha256:")
    assert report["next_recommended_step"].startswith("S2 -")
