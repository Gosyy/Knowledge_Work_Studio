from __future__ import annotations

from pathlib import Path

from scripts.kw_path_portability_policy_check import build_report


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_kr3a_path_portability_policy_is_ready() -> None:
    report = build_report(REPO_ROOT)

    assert report["status"] == "ready"
    assert report["summary"]["blocking_findings_total"] == 0
    assert report["summary"]["required_policy_files_missing"] == 0
    assert report["issues"] == []
