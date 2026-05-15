from __future__ import annotations

from pathlib import Path

from scripts.kw_path_portability_cleanup_plan import build_cleanup_plan


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_path_portability_cleanup_plan_is_ready_for_current_legacy_debt() -> None:
    report = build_cleanup_plan(REPO_ROOT)

    assert report["status"] == "ready"
    assert report["summary"]["legacy_findings_total"] > 0
    assert report["summary"]["cleanup_batch_count"] > 0
    assert report["summary"]["required_plan_files_missing"] == 0
    assert report["summary"]["physical_docs_codex_archive_allowed"] is False
    assert report["issues"] == []


def test_path_portability_cleanup_plan_classifies_stage_baseline_pins(tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "kw_s9_stage_quality_check.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        'EXPECTED_BASE = "0123456789abcdef0123456789abcdef01234567"\n'
        'BRANCH = "9_Product_Release_Hardening"\n',
        encoding="utf-8",
    )

    report = build_cleanup_plan(tmp_path)

    assert report["counts_by_batch"]["legacy_stage_baseline_pin_retirement"] == 2
    item = report["cleanup_items"][0]
    assert item["action"] == "archive_or_reclassify_stage_checker_after_product_replacement"


def test_path_portability_cleanup_plan_classifies_local_examples(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "refactor" / "OLD_RUNBOOK.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("Old command: cd /home/editor/workplace/Knowledge_Work_Studio\n", encoding="utf-8")

    report = build_cleanup_plan(tmp_path)

    assert report["counts_by_batch"]["local_example_rewrite_or_mark"] == 1
    assert report["cleanup_items"][0]["action"] == "rewrite as placeholders or mark as explicit local-only example"
