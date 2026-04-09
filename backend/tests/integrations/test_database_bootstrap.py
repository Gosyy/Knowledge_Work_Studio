from pathlib import Path

from backend.app.integrations.database import bootstrap_database


def test_bootstrap_database_applies_baseline_and_tracks_migration(tmp_path: Path) -> None:
    db_path = tmp_path / "metadata.sqlite3"
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)
    baseline = migrations_dir / "0001_baseline.sql"
    baseline.write_text(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        );
        """,
        encoding="utf-8",
    )

    database = bootstrap_database(db_path=db_path, migrations_dir=migrations_dir)

    with database.connect() as connection:
        sessions_table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'sessions'"
        ).fetchone()
        migration_record = connection.execute(
            "SELECT version FROM schema_migrations WHERE version = ?",
            ("0001_baseline.sql",),
        ).fetchone()

    assert sessions_table is not None
    assert migration_record is not None


def test_bootstrap_database_is_idempotent_for_applied_migrations(tmp_path: Path) -> None:
    db_path = tmp_path / "metadata.sqlite3"
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)
    migration = migrations_dir / "0001_baseline.sql"
    migration.write_text(
        """
        CREATE TABLE IF NOT EXISTS marker (
            id INTEGER PRIMARY KEY
        );
        """,
        encoding="utf-8",
    )

    database = bootstrap_database(db_path=db_path, migrations_dir=migrations_dir)
    database = bootstrap_database(db_path=db_path, migrations_dir=migrations_dir)

    with database.connect() as connection:
        versions = connection.execute(
            "SELECT version FROM schema_migrations WHERE version = ?",
            ("0001_baseline.sql",),
        ).fetchall()

    assert len(versions) == 1
