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
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                owner_user_id TEXT NOT NULL DEFAULT 'user_local_default',
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                owner_user_id TEXT NOT NULL DEFAULT 'user_local_default',
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
                owner_user_id TEXT NOT NULL DEFAULT 'user_local_default',
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                storage_backend TEXT NOT NULL DEFAULT 'local',
                storage_key TEXT NOT NULL DEFAULT '',
                storage_uri TEXT NOT NULL DEFAULT '',
                file_id TEXT,
                artifact_type TEXT NOT NULL DEFAULT 'other',
                title TEXT,
                size_bytes INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cursor.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS file_id TEXT")
        cursor.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS artifact_type TEXT NOT NULL DEFAULT 'other'")
        cursor.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS title TEXT")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                owner_user_id TEXT NOT NULL DEFAULT 'user_local_default',
                original_filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                storage_backend TEXT NOT NULL DEFAULT 'local',
                storage_key TEXT NOT NULL DEFAULT '',
                storage_uri TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stored_files (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL,
                owner_user_id TEXT NOT NULL DEFAULT 'user_local_default',
                kind TEXT NOT NULL,
                file_type TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                title TEXT,
                original_filename TEXT,
                storage_backend TEXT NOT NULL,
                storage_key TEXT NOT NULL,
                storage_uri TEXT NOT NULL,
                checksum_sha256 TEXT,
                size_bytes BIGINT,
                is_remote BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT stored_files_size_nonnegative_check
                    CHECK (size_bytes IS NULL OR size_bytes >= 0)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                current_file_id TEXT REFERENCES stored_files(id) ON DELETE SET NULL,
                document_type TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_versions (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                file_id TEXT NOT NULL REFERENCES stored_files(id) ON DELETE RESTRICT,
                version_number INTEGER NOT NULL,
                created_from_task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL,
                parent_version_id TEXT REFERENCES document_versions(id) ON DELETE SET NULL,
                change_summary TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT document_versions_version_number_positive_check
                    CHECK (version_number > 0)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS presentations (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                current_file_id TEXT REFERENCES stored_files(id) ON DELETE SET NULL,
                presentation_type TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS presentation_versions (
                id TEXT PRIMARY KEY,
                presentation_id TEXT NOT NULL REFERENCES presentations(id) ON DELETE CASCADE,
                file_id TEXT NOT NULL REFERENCES stored_files(id) ON DELETE RESTRICT,
                version_number INTEGER NOT NULL,
                created_from_task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL,
                parent_version_id TEXT REFERENCES presentation_versions(id) ON DELETE SET NULL,
                change_summary TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT presentation_versions_version_number_positive_check
                    CHECK (version_number > 0)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS artifact_sources (
                id TEXT PRIMARY KEY,
                artifact_id TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
                source_file_id TEXT REFERENCES stored_files(id) ON DELETE SET NULL,
                source_document_id TEXT REFERENCES documents(id) ON DELETE SET NULL,
                source_presentation_id TEXT REFERENCES presentations(id) ON DELETE SET NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT artifact_sources_at_least_one_source_check
                    CHECK (
                        source_file_id IS NOT NULL
                        OR source_document_id IS NOT NULL
                        OR source_presentation_id IS NOT NULL
                    )
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS derived_contents (
                id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL REFERENCES stored_files(id) ON DELETE CASCADE,
                content_kind TEXT NOT NULL,
                text_content TEXT,
                structured_json JSONB,
                outline_json JSONB,
                language TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_stored_files_storage_backend_key ON stored_files (storage_backend, storage_key)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_document_versions_doc_version ON document_versions (document_id, version_number)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_presentation_versions_presentation_version ON presentation_versions (presentation_id, version_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifact_sources_artifact_id ON artifact_sources (artifact_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_derived_contents_file_id ON derived_contents (file_id)")

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
