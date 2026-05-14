from __future__ import annotations

from pathlib import Path

from scripts.kw_product_docs_check import MANDATORY_WORKFLOWS, REQUIRED_DOCS, build_report


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_canonical_product_docs_are_ready_and_cover_required_workflows() -> None:
    report = build_report(REPO_ROOT)

    assert report["status"] == "ready"
    assert report["missing_doc_count"] == 0
    assert report["missing_workflows"] == []
    assert set(MANDATORY_WORKFLOWS).issubset(set(report["mandatory_workflows"]))
    assert "XLSX" in report["mandatory_workflows"]


def test_canonical_product_docs_are_not_stage_history_or_machine_local_runbooks() -> None:
    checked_paths = [REPO_ROOT / path for path in REQUIRED_DOCS.values()]
    forbidden_markers = (
        "/home/editor",
        "/home/su4ka",
        "Profile 1",
        "Profile 2",
        "profile1",
        "profile2",
        "Загрузки",
    )

    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        for marker in forbidden_markers:
            assert marker not in text, f"{path.relative_to(REPO_ROOT)} contains non-portable marker {marker!r}"
