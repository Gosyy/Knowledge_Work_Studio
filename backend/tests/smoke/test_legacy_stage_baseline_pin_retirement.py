from __future__ import annotations

from pathlib import Path

from scripts.kw_legacy_stage_baseline_pin_retirement import build_retirement_report


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_kr3c_legacy_stage_baseline_pin_retirement_batch1_is_ready() -> None:
    report = build_retirement_report(REPO_ROOT)

    assert report["status"] == "ready"
    assert report["summary"]["batch1_paths_selected"] > 0
    assert report["summary"]["batch1_items_selected"] > 0
    assert report["summary"]["required_retirement_files_missing"] == 0
    assert report["summary"]["physical_docs_codex_archive_allowed"] is False
    assert report["issues"] == []
