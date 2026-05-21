from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "kw_s2_outline_first_frontend_workflow_check.py"


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


def test_s2_outline_first_frontend_contract_is_ready() -> None:
    report = run_checker()
    assert report["status"] == "ready"
    assert report["outline_first_frontend_workflow_completed_by_s2"] is True
    assert report["frontend_workflow_contract_ready_by_s2"] is True
    assert report["frontend_journey_step_count"] == 9
    assert report["required_safe_task_event_count"] == 10


def test_s2_requires_editable_approved_plan_before_generation() -> None:
    report = run_checker()
    assert report["outline_visible_before_generation_by_s2"] is True
    assert report["editable_plan_required_before_generation_by_s2"] is True
    assert report["explicit_plan_approval_required_by_s2"] is True
    assert report["generation_requires_approved_plan_by_s2"] is True
    assert report["direct_pptx_generation_without_plan_allowed_by_s2"] is False


def test_s2_preserves_retry_and_render_mode_controls() -> None:
    report = run_checker()
    assert report["supported_render_modes_by_s2"] == ["adaptive", "template"]
    assert report["explicit_render_mode_required_by_s2"] is True
    assert report["plan_snapshot_required_by_s2"] is True
    assert report["retry_from_saved_plan_required_by_s2"] is True
    assert "slides.retry.from_saved_plan.requested" in report["required_safe_task_events"]


def test_s2_preserves_offline_and_no_parity_claim_boundaries() -> None:
    report = run_checker()
    assert report["frontend_runtime_changed_by_s2"] is False
    assert report["api_endpoint_added_by_s2"] is False
    assert report["db_schema_migration_added_by_s2"] is False
    assert report["network_required_for_s2"] is False
    assert report["server3_local_intranet_route_verified_by_s2"] is False
    assert report["kimi_slides_class_goal_advanced_by_s2"] is True
    assert report["kimi_slides_class_parity_claim_supported_by_s2"] is False
    assert report["kimi_level_claimed_by_s2"] is False
    assert report["next_recommended_step"].startswith("S3")
