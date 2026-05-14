from __future__ import annotations

from pathlib import Path

from scripts.kw_stage_checker_dependency_inventory import build_report


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_stage_dependency_inventory_keeps_docs_codex_archive_blocked_until_replacements() -> None:
    report = build_report(REPO_ROOT)
    summary = report["summary"]

    assert report["status"] == "ready"
    assert summary["physical_archive_blocked"] is True
    assert summary["direct_dependency_count"] > 0
    assert summary["unique_docs_codex_references"] > 0
    assert report["rewrite_order"]


def test_stage_dependency_inventory_points_to_product_replacement_targets() -> None:
    report = build_report(REPO_ROOT)
    rewrite_order = report["rewrite_order"]

    targets = {
        item.get("product_test_target")
        for item in rewrite_order
        if item.get("product_test_target")
    }
    assert any("backend/tests/operators/" in target for target in targets)
    assert any("backend/tests/workflows/" in target for target in targets)
    assert any("backend/tests/quality/" in target for target in targets)
