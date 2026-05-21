from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from scripts.kw_operator_log_archive import archive_log_dir


def test_log_archive_creates_zip_with_relative_entries_and_removes_source(tmp_path: Path) -> None:
    log_parent = tmp_path / "logs"
    log_dir = log_parent / "run-001"
    nested = log_dir / "nested"
    nested.mkdir(parents=True)
    (log_dir / "main.log").write_text("hello\n", encoding="utf-8")
    (nested / "details.txt").write_text("details\n", encoding="utf-8")

    zip_path = tmp_path / "artifacts" / "run-001.logs.zip"
    result = archive_log_dir(log_dir, zip_path)

    assert result == zip_path.resolve()
    assert zip_path.exists()
    assert not log_dir.exists()

    with ZipFile(zip_path, "r") as archive:
        names = set(archive.namelist())

    assert "run-001/main.log" in names
    assert "run-001/nested/details.txt" in names


def test_log_archive_can_keep_source_for_diagnostics(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs" / "run-keep"
    log_dir.mkdir(parents=True)
    (log_dir / "main.log").write_text("keep me\n", encoding="utf-8")

    zip_path = tmp_path / "run-keep.zip"
    archive_log_dir(log_dir, zip_path, remove_source=False)

    assert zip_path.exists()
    assert log_dir.exists()
    assert (log_dir / "main.log").read_text(encoding="utf-8") == "keep me\n"
