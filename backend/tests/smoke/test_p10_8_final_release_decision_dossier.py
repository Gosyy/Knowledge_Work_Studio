from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "kw_p10_8_final_release_decision_dossier.py"


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


def test_p10_8_dossier_is_ready_without_release_approval() -> None:
    report = run_checker()
    assert report["status"] == "ready"
    assert report["completed_human_review_decision_count"] == 5
    assert report["approve_count"] == 4
    assert report["request_rework_count"] == 1
    assert report["reject_count"] == 0
    assert report["final_release_decision_by_p10_8"] == "defer_pending_targeted_rework"
    assert report["release_approval_granted_by_p10_8"] is False
    assert report["release_approval_supported_by_p10_8"] is False
    assert report["approval_state_changed_by_p10_8"] is False
    assert report["golden_decks_auto_approved_by_p10_8"] is False
    assert report["kimi_level_claimed_by_p10_8"] is False


def test_p10_8_preserves_review_blocker_and_backlog() -> None:
    report = run_checker()
    assert report["blocking_case_ids"] == ["k0_arch_doc_to_architecture_deck"]
    assert report["architecture_case_requires_targeted_rework_or_owner_waiver"] is True
    assert report["follow_up_backlog_item_count"] == 3
    assert any(item["priority"] == "P0" for item in report["follow_up_backlog"])


def test_p10_8_preserves_gigachat_boundary() -> None:
    report = run_checker()
    assert report["project_completion_can_use_public_api_dev_gigachat_evidence"] is True
    assert report["p10_5a_public_api_dev_evidence_is_real_provider_evidence"] is True
    assert report["p10_5a_public_api_dev_evidence_is_not_server3_offline_proof"] is True
    assert report["server3_local_intranet_verification_required_for_p10_8"] is False
    assert report["server3_local_intranet_route_verified_by_p10_8"] is False
    assert report["production_offline_mode_remains_target_deployment_mode"] is True
    assert report["network_required_for_p10_8"] is False


def test_p10_8_can_persist_dossier(tmp_path: Path) -> None:
    out_dir = tmp_path / "p10-8"
    report = run_checker("--artifacts-dir", str(out_dir))
    dossier_path = Path(report["p10_8_dossier_file"])
    assert dossier_path.exists()
    persisted = json.loads(dossier_path.read_text(encoding="utf-8"))
    assert persisted["p10_8_dossier_digest"].startswith("sha256:")
    assert persisted["final_release_decision_by_p10_8"] == "defer_pending_targeted_rework"
