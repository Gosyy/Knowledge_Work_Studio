from __future__ import annotations

from pathlib import Path

from backend.app.integrations.database.sqlite import SQLiteDatabase


def bootstrap_database(*, db_path: Path, migrations_dir: Path) -> SQLiteDatabase:
    database = SQLiteDatabase(db_path=db_path)
    database.initialize()
    apply_migrations(database=database, migrations_dir=migrations_dir)
    return database


def apply_migrations(*, database: SQLiteDatabase, migrations_dir: Path) -> None:
    if not migrations_dir.exists():
        return

    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        return

    with database.connect() as connection:
        applied_versions = {
            str(row["version"])
            for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
        }

        for migration_file in migration_files:
            version = migration_file.name
            if version in applied_versions:
                continue

            sql = migration_file.read_text(encoding="utf-8")
            connection.executescript(sql)
            connection.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)",
                (version,),
            )
        connection.commit()
