from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from backend.app.core.config import Settings

logger = logging.getLogger(__name__)

BASELINE_VERSION = "0001_repository_baseline"


def _database_path(settings: Settings) -> Path:
    return Path(settings.repository_db_path)


def apply_sqlite_baseline(db_path: Path, baseline_sql_path: Path, version: str = BASELINE_VERSION) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        already_applied = connection.execute(
            "SELECT 1 FROM schema_migrations WHERE version = ?",
            (version,),
        ).fetchone()

        if already_applied:
            logger.debug("Baseline migration %s already applied", version)
            return

        baseline_sql = baseline_sql_path.read_text(encoding="utf-8")
        connection.executescript(baseline_sql)
        connection.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
        logger.info("Applied baseline migration %s", version)


def initialize_database(settings: Settings) -> None:
    db_path = _database_path(settings)
    baseline_sql_path = Path(settings.migration_baseline_path)

    if not baseline_sql_path.exists():
        raise FileNotFoundError(f"Baseline migration SQL file not found: {baseline_sql_path}")

    apply_sqlite_baseline(db_path=db_path, baseline_sql_path=baseline_sql_path)
