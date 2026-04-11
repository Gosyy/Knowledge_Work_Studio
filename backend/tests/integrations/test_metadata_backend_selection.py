from pathlib import Path

import pytest

from backend.app.core.config import Settings
from backend.app.integrations.database.bootstrap import initialize_database


def test_initialize_database_rejects_sqlite_when_not_explicitly_allowed(tmp_path: Path) -> None:
    baseline_sql = tmp_path / "0001.sql"
    baseline_sql.write_text(
        "CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, created_at TEXT NOT NULL);",
        encoding="utf-8",
    )

    settings = Settings(
        metadata_backend="sqlite",
        sqlite_runtime_allowed=False,
        repository_db_path=str(tmp_path / "repositories.sqlite3"),
        migration_baseline_path=str(baseline_sql),
    )

    with pytest.raises(ValueError, match="SQLite metadata backend is disabled"):
        initialize_database(settings)


def test_initialize_database_accepts_sqlite_when_explicitly_allowed(tmp_path: Path) -> None:
    baseline_sql = tmp_path / "0001.sql"
    baseline_sql.write_text(
        "CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, created_at TEXT NOT NULL);",
        encoding="utf-8",
    )

    settings = Settings(
        metadata_backend="sqlite",
        sqlite_runtime_allowed=True,
        repository_db_path=str(tmp_path / "repositories.sqlite3"),
        migration_baseline_path=str(baseline_sql),
    )

    initialize_database(settings)


def test_initialize_database_rejects_sqlite_in_production_env_even_if_allowed(tmp_path: Path) -> None:
    baseline_sql = tmp_path / "0001.sql"
    baseline_sql.write_text(
        "CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, created_at TEXT NOT NULL);",
        encoding="utf-8",
    )

    settings = Settings(
        app_env="production",
        metadata_backend="sqlite",
        sqlite_runtime_allowed=True,
        repository_db_path=str(tmp_path / "repositories.sqlite3"),
        migration_baseline_path=str(baseline_sql),
    )

    with pytest.raises(ValueError, match="only allowed in development/test environments"):
        initialize_database(settings)
