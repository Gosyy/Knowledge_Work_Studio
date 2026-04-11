from pathlib import Path

from backend.app.core.config import Settings
from backend.app.integrations.database import BASELINE_VERSION, initialize_database


def test_initialize_database_applies_baseline_idempotently(tmp_path: Path) -> None:
    db_path = tmp_path / "repos.sqlite3"
    baseline_sql = tmp_path / "0001.sql"
    baseline_sql.write_text(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        );
        """,
        encoding="utf-8",
    )

    settings = Settings(
        metadata_backend="sqlite",
        sqlite_runtime_allowed=True,
        repository_db_path=str(db_path),
        migration_baseline_path=str(baseline_sql),
    )

    initialize_database(settings)
    initialize_database(settings)

    import sqlite3

    with sqlite3.connect(db_path) as connection:
        migration_row = connection.execute(
            "SELECT version FROM schema_migrations WHERE version = ?",
            (BASELINE_VERSION,),
        ).fetchone()
        assert migration_row is not None

        sessions_table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'sessions'"
        ).fetchone()
        assert sessions_table is not None
