from __future__ import annotations

from pathlib import Path

from scripts.kw_product_test_aliases_check import (
    LEGACY_BRIDGE_CHECKS,
    REQUIRED_PRODUCT_DOCS,
    REQUIRED_PRODUCT_TEST_FILES,
    build_product_test_aliases_report,
)


def _touch_all(root: Path, paths: list[str] | tuple[str, ...]) -> None:
    for path in paths:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("placeholder\n", encoding="utf-8")


def test_product_test_alias_report_is_ready_for_complete_synthetic_repo(tmp_path: Path) -> None:
    _touch_all(tmp_path, REQUIRED_PRODUCT_TEST_FILES)
    _touch_all(tmp_path, REQUIRED_PRODUCT_DOCS)
    for paths in LEGACY_BRIDGE_CHECKS.values():
        _touch_all(tmp_path, paths)

    report = build_product_test_aliases_report(tmp_path)

    assert report["status"] == "ready"
    assert report["product_test_aliases_ready"] is True
    assert report["product_docs_ready"] is True
    assert report["legacy_bridge_aliases_ready"] is True
    assert report["physical_docs_archive_blocked"] is True


def test_product_test_alias_report_blocks_missing_product_aliases(tmp_path: Path) -> None:
    _touch_all(tmp_path, REQUIRED_PRODUCT_DOCS)
    for paths in LEGACY_BRIDGE_CHECKS.values():
        _touch_all(tmp_path, paths)

    report = build_product_test_aliases_report(tmp_path)

    assert report["status"] == "blocked"
    assert report["product_test_aliases_ready"] is False
    assert any("missing product test alias" in issue for issue in report["issues"])
