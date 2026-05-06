from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_p9_7_golden_review_readiness_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_p9_7_checker_reports_ready_without_scope_escape() -> None:
    result = run_check("--json", "--require-ready")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P9-7"
    assert payload["status"] == "ready"
    assert payload["p9_7_golden_review_readiness_supported"] is True
    assert payload["post_hardening_re_review_packet_supported"] is True
    assert payload["human_review_replay_required"] is True
    assert payload["golden_case_count"] == 5
    assert payload["re_review_case_count"] == 5
    assert payload["original_request_rework_count"] == 5
    assert payload["original_approve_count"] == 0
    assert payload["approval_state_changed_by_p9_7"] is False
    assert payload["human_review_results_fabricated_by_p9_7"] is False
    assert payload["api_endpoint_added_by_p9_7"] is False
    assert payload["db_schema_migration_added_by_p9_7"] is False
    assert payload["frontend_runtime_changed_by_p9_7"] is False
    assert payload["dependency_versions_changed_by_p9_7"] is False
    assert payload["dockerfiles_changed_by_p9_7"] is False
    assert payload["cloud_llm_added_by_p9_7"] is False
    assert payload["cloud_vision_added_by_p9_7"] is False
    assert payload["kimi_level_claimed_by_p9_7"] is False
    assert payload["whole_project_kimi_level_supported"] is False


def test_p9_7_maps_all_prior_hardening_evidence_to_re_review_cases() -> None:
    result = run_check("--json", "--require-ready")
    payload = json.loads(result.stdout)
    evidence = set(payload["hardening_evidence_ids"])
    assert {"P9-2", "P9-3", "P9-4", "P9-5", "P9-6"}.issubset(evidence)
    cards = payload["case_readiness_cards"]
    assert len(cards) == 5
    assert {card["case_id"] for card in cards} == {
        "k0_exec_memo_to_board_deck",
        "k0_arch_doc_to_architecture_deck",
        "k0_project_log_to_status_deck",
        "k0_comparison_table_to_decision_deck",
        "k0_long_docx_pdf_to_structured_presentation",
    }
    for card in cards:
        assert card["original_decision"] == "request_rework"
        assert card["requires_human_re_review"] is True
        assert card["hardening_evidence_ids"]
        assert "Regenerate or re-open" in card["operator_review_instruction"]


def test_p9_7_keeps_original_human_review_fixture_conservative() -> None:
    fixture = json.loads((repo_root() / "backend/tests/fixtures/p9/p9_1_human_review_results.json").read_text(encoding="utf-8"))
    assert fixture["human_review_results_completed"] is True
    assert fixture["human_review_summary"]["decision_counts"] == {"approve": 0, "reject": 0, "request_rework": 5}
    assert fixture["kimi_level_claimed"] is False
    assert fixture["whole_project_kimi_level_supported"] is False
    assert all(case["decision"] == "request_rework" for case in fixture["cases"])
