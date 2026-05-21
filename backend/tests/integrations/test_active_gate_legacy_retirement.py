from __future__ import annotations

from pathlib import Path

from scripts.kw_active_gate_legacy_retirement_check import (
    REQUIRED_ACTIVE_REPLACEMENT_CHECKS,
    RETIRED_ACTIVE_GATE_SCRIPTS,
    build_report,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_kr3e_report_is_ready_on_repository_tree() -> None:
    report = build_report(REPO_ROOT)
    assert report["status"] == "ready", report["issues"]
    assert report["retired_still_in_gate_count"] == 0
    assert report["missing_replacement_checks_count"] == 0


def test_production_gate_does_not_reference_retired_legacy_stage_checkers() -> None:
    gate = (REPO_ROOT / "scripts" / "kw_production_readiness_gate.py").read_text(encoding="utf-8")
    for rel in RETIRED_ACTIVE_GATE_SCRIPTS:
        assert rel not in gate


def test_production_gate_runs_product_replacement_checks() -> None:
    gate = (REPO_ROOT / "scripts" / "kw_production_readiness_gate.py").read_text(encoding="utf-8")
    for rel in REQUIRED_ACTIVE_REPLACEMENT_CHECKS:
        assert rel in gate
