from __future__ import annotations

from pathlib import Path

from scripts.kw_slides_product_quality_replacements_check import build_report


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_kr2e_slides_product_quality_replacements_are_ready() -> None:
    report = build_report(REPO_ROOT)
    assert report["status"] == "ready"
    assert report["summary"]["product_slides_tests_ready"] == report["summary"]["product_slides_tests_required"]
    assert report["summary"]["product_slides_docs_ready"] == report["summary"]["product_slides_docs_checked"]
    assert report["summary"]["physical_docs_codex_archive_allowed"] is False
    assert report["issues"] == []
