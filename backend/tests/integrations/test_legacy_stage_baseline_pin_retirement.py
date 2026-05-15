from __future__ import annotations

from pathlib import Path

from scripts.kw_legacy_stage_baseline_pin_retirement import (
    build_retirement_report,
    build_stage_pin_groups,
    select_batch1,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_legacy_stage_baseline_pin_retirement_batch1_is_ready_for_current_repo() -> None:
    report = build_retirement_report(REPO_ROOT)

    assert report["status"] == "ready"
    assert report["summary"]["legacy_stage_baseline_pin_items_total"] > 0
    assert report["summary"]["legacy_stage_baseline_pin_paths_total"] > 0
    assert report["summary"]["batch1_paths_selected"] > 0
    assert report["summary"]["batch1_items_selected"] > 0
    assert report["summary"]["execution_mode"] == "retirement_manifest_and_reclassification"
    assert report["summary"]["physical_docs_codex_archive_allowed"] is False
    assert report["issues"] == []


def test_batch1_selection_prefers_inactive_stage_checkers_before_active_referenced_ones(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir(parents=True)

    sha_value = "0123456789abcdef" + "0123456789abcdef" + "01234567"
    branch_value = "9_" + "Product_Release_Hardening"

    inactive = scripts / "kw_s9_inactive_quality_check.py"
    inactive.write_text(
        f'EXPECTED_BASE = "{sha_value}"\n'
        f'BRANCH = "{branch_value}"\n',
        encoding="utf-8",
    )

    active = scripts / "kw_k3_active_quality_check.py"
    active.write_text(
        f'EXPECTED_BASE = "{sha_value}"\n'
        f'BRANCH = "{branch_value}"\n',
        encoding="utf-8",
    )
    (scripts / "kw_production_readiness_gate.py").write_text(
        '"scripts/kw_k3_active_quality_check.py"\n',
        encoding="utf-8",
    )

    groups = build_stage_pin_groups(tmp_path)
    selected = select_batch1(groups, max_paths=1)

    assert len(selected) == 1
    assert selected[0].path == "scripts/kw_s9_inactive_quality_check.py"
    assert selected[0].active_reference_count == 0


def test_active_referenced_stage_checker_is_reclassified_not_edited(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir(parents=True)

    sha_value = "abcdef0123456789" + "abcdef0123456789" + "abcdef01"
    branch_value = "9_" + "Product_Release_Hardening"

    checker = scripts / "kw_k6_active_workflow_check.py"
    checker.write_text(
        f'EXPECTED_BASE = "{sha_value}"\n'
        f'BRANCH = "{branch_value}"\n',
        encoding="utf-8",
    )
    (scripts / "kw_production_readiness_gate.py").write_text(
        '"scripts/kw_k6_active_workflow_check.py"\n',
        encoding="utf-8",
    )

    groups = build_stage_pin_groups(tmp_path)

    assert len(groups) == 1
    assert groups[0].active_reference_count == 1
    assert groups[0].batch1_action == "reclassify_as_legacy_safety_net_before_editing"
