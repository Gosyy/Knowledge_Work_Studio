from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "kw_p10_9_targeted_architecture_rework.py"


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
def p10_9_report(tmp_path_factory: pytest.TempPathFactory) -> dict:
    out_dir = tmp_path_factory.mktemp("p10_9") / "artifacts"
    return run_checker("--artifacts-dir", str(out_dir))


def test_p10_9_resolves_architecture_rework_without_release_approval(p10_9_report: dict) -> None:
    report = p10_9_report
    assert report["status"] == "ready"
    assert report["targeted_case_id"] == "k0_arch_doc_to_architecture_deck"
    assert report["p10_8_previous_release_decision"] == "defer_pending_targeted_rework"
    assert report["p10_8_previous_blocking_case_ids"] == ["k0_arch_doc_to_architecture_deck"]
    assert report["architecture_request_rework_resolved_by_p10_9"] is True
    assert report["targeted_architecture_re_review_decision_by_p10_9"] == "approve"
    assert report["approve_count_after_p10_9"] == 5
    assert report["request_rework_count_after_p10_9"] == 0
    assert report["release_decision_supported_after_p10_9"] == "ready_for_final_release_approval_dossier"
    assert report["release_approval_granted_by_p10_9"] is False
    assert report["final_release_approval_requires_p10_10"] is True


def test_p10_9_architecture_deck_has_guarded_storyline(p10_9_report: dict) -> None:
    report = p10_9_report
    titles = report["targeted_architecture_artifact_summary"]["slide_titles"]
    assert titles == [
        "Architecture review: offline KW Studio topology",
        "Topology map: Server 1/2/3 responsibilities",
        "Production path: direct local GigaChat",
        "Server 2 boundary: optional gateway and heavy runtime",
        "Closed foundation controls: deployment and diagnostics",
        "Runtime capabilities: plan, render, QA, provenance",
        "Failure modes and operator gates",
        "Release readiness checks and ownership",
    ]
    assert report["targeted_architecture_artifact_summary"]["slide_7_title"] == "Failure modes and operator gates"
    assert not any(title.startswith(("Opening:", "Context:")) for title in titles)


def test_p10_9_preserves_offline_and_gigachat_boundaries(p10_9_report: dict) -> None:
    report = p10_9_report
    assert report["project_completion_can_use_public_api_dev_gigachat_evidence"] is True
    assert report["p10_5a_public_api_dev_evidence_is_not_server3_offline_proof"] is True
    assert report["server3_local_intranet_verification_required_for_p10_9"] is False
    assert report["server3_local_intranet_route_verified_by_p10_9"] is False
    assert report["network_required_for_p10_9"] is False
    assert report["kimi_level_claimed_by_p10_9"] is False
    assert report["whole_project_kimi_level_supported"] is False


def test_p10_9_can_persist_targeted_evidence(p10_9_report: dict) -> None:
    report = p10_9_report
    assert Path(report["p10_9_report_file"]).exists()
    artifacts_root = Path(report["artifacts_root"])
    assert (artifacts_root / "k0_arch_doc_to_architecture_deck" / "rc1-k0_arch_doc_to_architecture_deck.pptx").exists()
    assert (artifacts_root / "k0_arch_doc_to_architecture_deck" / "manifest.json").exists()
    assert report["targeted_architecture_artifact_summary"]["pptx_sha256"].startswith("sha256:")
