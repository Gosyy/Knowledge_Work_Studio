from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

from backend.app.core.config import Settings

logger = logging.getLogger(__name__)

BASELINE_VERSION = "0001_repository_baseline"


def _database_path(settings: Settings) -> Path:
    return Path(settings.repository_db_path)


def _normalize_database_url(database_url: str) -> str:
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def _require_psycopg() -> Any:
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "psycopg is required for metadata_backend=postgres. "
            "Install psycopg or use explicit sqlite test mode "
            "(METADATA_BACKEND=sqlite and SQLITE_RUNTIME_ALLOWED=true)."
        ) from exc
    return psycopg


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


def apply_postgres_baseline(database_url: str, version: str = BASELINE_VERSION) -> None:
    psycopg = _require_psycopg()
    dsn = _normalize_database_url(database_url)

    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute("SELECT 1 FROM schema_migrations WHERE version = %s", (version,))
        already_applied = cursor.fetchone() is not None

        if already_applied:
            logger.debug("Postgres baseline migration %s already applied", version)
            connection.commit()
            return

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                error_message TEXT,
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                storage_path TEXT NOT NULL DEFAULT '',
                size_bytes INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cursor.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))
        logger.info("Applied Postgres baseline migration %s", version)
        connection.commit()


def initialize_database(settings: Settings) -> None:
    backend = settings.metadata_backend.lower()
    if backend == "sqlite" and not settings.sqlite_runtime_allowed:
        raise ValueError(
            "SQLite metadata backend is disabled for runtime usage. "
            "Use METADATA_BACKEND=postgres (default production truth layer), "
            "or explicitly set SQLITE_RUNTIME_ALLOWED=true for tests."
        )
    if backend == "sqlite" and settings.app_env.lower() not in {"development", "test"}:
        raise ValueError(
            "SQLite metadata backend is only allowed in development/test environments. "
            "Use METADATA_BACKEND=postgres for production runtime."
        )

    if backend == "postgres":
        apply_postgres_baseline(settings.database_url)
        return

    if backend == "sqlite":
        db_path = _database_path(settings)
        baseline_sql_path = Path(settings.migration_baseline_path)

        if not baseline_sql_path.exists():
            raise FileNotFoundError(f"Baseline migration SQL file not found: {baseline_sql_path}")

        apply_sqlite_baseline(db_path=db_path, baseline_sql_path=baseline_sql_path)
        return

    raise ValueError(f"Unsupported metadata backend: {settings.metadata_backend}")
