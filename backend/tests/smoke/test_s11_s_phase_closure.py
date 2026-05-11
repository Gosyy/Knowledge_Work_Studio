from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.slides_service.s_phase_closure import s_phase_closure_report

REPO_ROOT = Path(__file__).resolve().parents[2].parent


def test_s11_s_phase_closure_report_ready() -> None:
    report = s_phase_closure_report()
    assert report["status"] == "ready"
    assert report["s_phase_closure_completed_by_s11"] is True
    assert report["s1_to_s10_capability_track_closed_by_s11"] is True
    assert report["closed_s_phase_count"] == 10
    assert report["s10_scenario_count_confirmed_by_s11"] == 12


def test_s11_keeps_parity_claim_future_only() -> None:
    report = s_phase_closure_report()
    assert report["accepted_future_claim_wording_by_s11"] == "Kimi Slides-class offline workflow parity for selected benchmark scenarios."
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s11"] is False
    assert report["selected_offline_workflow_parity_claim_requires_future_completed_results_by_s11"] is True
    assert report["completed_human_review_fabricated_by_s11"] is False


def test_s11_preserves_forbidden_claims_and_offline_boundaries() -> None:
    report = s_phase_closure_report()
    assert report["generic_kimi_level_achieved_claim_allowed_by_s11"] is False
    assert report["kimi_level_claimed_by_s11"] is False
    assert report["whole_project_kimi_level_supported"] is False
    assert report["server3_local_intranet_route_verified_by_s11"] is False
    assert report["hidden_public_internet_allowed_by_s11"] is False
    assert report["cloud_research_allowed_by_s11"] is False
    assert report["cloud_vision_allowed_by_s11"] is False


def test_s11_checker_json_ready() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/kw_s11_s_phase_closure_check.py", "--repo-root", str(REPO_ROOT), "--json"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["s_phase_closure_completed_by_s11"] is True
