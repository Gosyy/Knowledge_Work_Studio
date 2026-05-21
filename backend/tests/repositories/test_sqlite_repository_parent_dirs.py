from __future__ import annotations

from backend.app.repositories.sqlite import SqliteSessionRepository, SqliteTaskRepository


def test_sqlite_repository_creates_missing_parent_directory_before_connect(tmp_path):
    db_path = tmp_path / "missing" / "nested" / "repositories.sqlite3"

    assert not db_path.parent.exists()

    SqliteSessionRepository(str(db_path))

    assert db_path.parent.is_dir()
    assert db_path.exists()

    # A second repository type should reuse the same newly-created location
    # rather than surfacing sqlite3.OperationalError on fresh profiles.
    SqliteTaskRepository(str(db_path))
