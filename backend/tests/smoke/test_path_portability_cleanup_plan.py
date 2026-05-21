from __future__ import annotations

from pathlib import Path

from scripts.kw_path_portability_cleanup_plan import build_cleanup_plan


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_kr3b_path_portability_cleanup_plan_is_ready() -> None:
    report = build_cleanup_plan(REPO_ROOT)

    assert report["status"] == "ready"
    assert report["summary"]["legacy_findings_total"] == report["summary"]["legacy_warn_only_total_from_policy_scanner"]
    assert report["summary"]["cleanup_batch_count"] >= 1
    assert report["summary"]["physical_docs_codex_archive_allowed"] is False
    assert report["issues"] == []
