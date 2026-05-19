from __future__ import annotations

from pathlib import Path

from scripts.kw_controlled_archive_delete_readiness_check import (
    ARCHIVE_ROOT,
    BATCH1_ARCHIVE_MOVES,
    build_report,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_kr3f_archive_delete_readiness_report_is_ready() -> None:
    report = build_report(REPO_ROOT)
    assert report["status"] == "ready", report["issues"]
    assert report["moved_paths_count"] == len(BATCH1_ARCHIVE_MOVES)
    assert report["active_old_path_references_count"] == 0
    assert report["production_gate_references_checker"] is True


def test_kr3f_batch_moves_only_root_history_not_docs_codex() -> None:
    for old, new in BATCH1_ARCHIVE_MOVES:
        assert not old.startswith("docs/codex/")
        assert not new.startswith("docs/codex/")
        assert (REPO_ROOT / new).is_file()
        assert not (REPO_ROOT / old).exists()
    assert (REPO_ROOT / ARCHIVE_ROOT / "README.md").is_file()
    assert (REPO_ROOT / "docs" / "codex").is_dir()
