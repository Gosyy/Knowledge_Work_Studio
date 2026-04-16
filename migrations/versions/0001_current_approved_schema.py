"""current approved schema

Revision ID: 0001_current_approved_schema
Revises:
Create Date: 2026-04-16 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "0001_current_approved_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # M3 represents the accepted M2 Postgres truth-layer schema.
    # CREATE TABLE IF NOT EXISTS plus ADD COLUMN IF NOT EXISTS keeps this safe
    # for databases previously initialized by backend bootstrap.
    op.execute(
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

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            owner_user_id TEXT NOT NULL DEFAULT 'user_local_default',
            created_at TIMESTAMPTZ NOT NULL
        )
        """
    )
    op.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT 'user_local_default'")

    op.execute(
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
    op.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT 'user_local_default'")
    op.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS result_json JSONB NOT NULL DEFAULT '{}'::jsonb")
    op.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS error_message TEXT")
    op.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ")
    op.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ")

    op.execute(
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
    op.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT 'user_local_default'")
    op.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS storage_backend TEXT NOT NULL DEFAULT 'local'")
    op.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS storage_key TEXT NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS storage_uri TEXT NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS file_id TEXT")
    op.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS artifact_type TEXT NOT NULL DEFAULT 'other'")
    op.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS title TEXT")
    op.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS size_bytes INTEGER NOT NULL DEFAULT 0")

    op.execute(
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
    op.execute("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT 'user_local_default'")
    op.execute("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS storage_backend TEXT NOT NULL DEFAULT 'local'")
    op.execute("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS storage_key TEXT NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS storage_uri TEXT NOT NULL DEFAULT ''")

    op.execute(
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
    op.execute("ALTER TABLE stored_files ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT 'user_local_default'")

    op.execute(
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

    op.execute(
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

    op.execute(
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

    op.execute(
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

    op.execute(
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

    op.execute(
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

    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_stored_files_storage_backend_key ON stored_files (storage_backend, storage_key)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_document_versions_doc_version ON document_versions (document_id, version_number)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_presentation_versions_presentation_version ON presentation_versions (presentation_id, version_number)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_artifact_sources_artifact_id ON artifact_sources (artifact_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_derived_contents_file_id ON derived_contents (file_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_derived_contents_file_id")
    op.execute("DROP INDEX IF EXISTS idx_artifact_sources_artifact_id")
    op.execute("DROP INDEX IF EXISTS uq_presentation_versions_presentation_version")
    op.execute("DROP INDEX IF EXISTS uq_document_versions_doc_version")
    op.execute("DROP INDEX IF EXISTS uq_stored_files_storage_backend_key")

    op.execute("DROP TABLE IF EXISTS derived_contents")
    op.execute("DROP TABLE IF EXISTS artifact_sources")
    op.execute("DROP TABLE IF EXISTS presentation_versions")
    op.execute("DROP TABLE IF EXISTS presentations")
    op.execute("DROP TABLE IF EXISTS document_versions")
    op.execute("DROP TABLE IF EXISTS documents")
    op.execute("DROP TABLE IF EXISTS stored_files")
    op.execute("DROP TABLE IF EXISTS uploaded_files")
    op.execute("DROP TABLE IF EXISTS artifacts")
    op.execute("DROP TABLE IF EXISTS tasks")
    op.execute("DROP TABLE IF EXISTS sessions")
    op.execute("DROP TABLE IF EXISTS users")
