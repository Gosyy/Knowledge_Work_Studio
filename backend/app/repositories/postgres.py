from __future__ import annotations

import json
from datetime import datetime
from threading import Lock
from typing import Any

from backend.app.domain import (
    Artifact,
    ArtifactSource,
    DerivedContent,
    Document,
    DocumentVersion,
    Presentation,
    PresentationPlanSnapshot,
    PresentationVersion,
    Session,
    StoredFile,
    Task,
    TaskStatus,
    TaskType,
    UploadedFile,
    User,
)


def _normalize_database_url(database_url: str) -> str:
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def _require_psycopg() -> tuple[Any, Any]:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError(
            "psycopg is required for metadata_backend=postgres. "
            "Install psycopg or use explicit sqlite test mode "
            "(METADATA_BACKEND=sqlite and SQLITE_RUNTIME_ALLOWED=true)."
        ) from exc
    return psycopg, dict_row


def _parse_datetime(value: datetime) -> datetime:
    return value


class _PostgresRepositoryBase:
    def __init__(self, database_url: str) -> None:
        self._database_url = _normalize_database_url(database_url)
        self._lock = Lock()
        self._initialize_schema()

    def _connect(self):
        psycopg, dict_row = _require_psycopg()
        return psycopg.connect(self._database_url, row_factory=dict_row)

    def _initialize_schema(self) -> None:
        raise NotImplementedError


class PostgresUserRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
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
            connection.commit()

    def create(self, user: User) -> User:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users
                (id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    email = EXCLUDED.email,
                    password_hash = EXCLUDED.password_hash,
                    display_name = EXCLUDED.display_name,
                    is_active = EXCLUDED.is_active,
                    is_superuser = EXCLUDED.is_superuser,
                    created_at = EXCLUDED.created_at,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    user.id,
                    user.email,
                    user.password_hash,
                    user.display_name,
                    user.is_active,
                    user.is_superuser,
                    user.created_at,
                    user.updated_at,
                ),
            )
            connection.commit()
        return user

    def get(self, user_id: str) -> User | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return User(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            display_name=row["display_name"],
            is_active=row["is_active"],
            is_superuser=row["is_superuser"],
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def get_by_email(self, email: str) -> User | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at
                FROM users
                WHERE email = %s
                """,
                (email.strip().lower(),),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return User(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            display_name=row["display_name"],
            is_active=row["is_active"],
            is_superuser=row["is_superuser"],
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def list(self) -> list[User]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at
                FROM users
                ORDER BY created_at ASC
                """
            )
            rows = cursor.fetchall()
        return [
            User(
                id=row["id"],
                email=row["email"],
                password_hash=row["password_hash"],
                display_name=row["display_name"],
                is_active=row["is_active"],
                is_superuser=row["is_superuser"],
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]


class PostgresSessionRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
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
                "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT 'user_local_default'"
            )
        connection.commit()

    def create(self, session: Session) -> Session:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sessions (id, owner_user_id, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET owner_user_id = EXCLUDED.owner_user_id, created_at = EXCLUDED.created_at
                """,
                (session.id, session.owner_user_id, session.created_at),
            )
            connection.commit()
        return session

    def get(self, session_id: str) -> Session | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT id, owner_user_id, created_at FROM sessions WHERE id = %s", (session_id,))
            row = cursor.fetchone()
        if row is None:
            return None
        return Session(id=row["id"], owner_user_id=row["owner_user_id"], created_at=_parse_datetime(row["created_at"]))


class PostgresTaskRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
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
                "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT 'user_local_default'"
            )
            connection.commit()

    def create(self, task: Task) -> Task:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks
                (id, session_id, owner_user_id, task_type, status, result_json, error_message, started_at, completed_at, created_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    session_id = EXCLUDED.session_id,
                    owner_user_id = EXCLUDED.owner_user_id,
                    task_type = EXCLUDED.task_type,
                    status = EXCLUDED.status,
                    result_json = EXCLUDED.result_json,
                    error_message = EXCLUDED.error_message,
                    started_at = EXCLUDED.started_at,
                    completed_at = EXCLUDED.completed_at,
                    created_at = EXCLUDED.created_at
                """,
                (
                    task.id,
                    task.session_id,
                    task.owner_user_id,
                    task.task_type.value,
                    task.status.value,
                    json.dumps(task.result_data),
                    task.error_message,
                    task.started_at,
                    task.completed_at,
                    task.created_at,
                ),
            )
            connection.commit()
        return task

    def update(self, task: Task) -> Task:
        return self.create(task)

    def get(self, task_id: str) -> Task | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, session_id, owner_user_id, task_type, status, result_json, error_message, started_at, completed_at, created_at
                FROM tasks
                WHERE id = %s
                """,
                (task_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return Task(
            id=row["id"],
            session_id=row["session_id"],
            owner_user_id=row["owner_user_id"],
            task_type=TaskType(row["task_type"]),
            status=TaskStatus(row["status"]),
            result_data=row["result_json"] or {},
            error_message=row["error_message"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            created_at=row["created_at"],
        )

    def list_by_session(self, session_id: str) -> list[Task]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, session_id, owner_user_id, task_type, status, result_json, error_message, started_at, completed_at, created_at
                FROM tasks
                WHERE session_id = %s
                ORDER BY created_at ASC
                """,
                (session_id,),
            )
            rows = cursor.fetchall()

        return [
            Task(
                id=row["id"],
                session_id=row["session_id"],
                owner_user_id=row["owner_user_id"],
                task_type=TaskType(row["task_type"]),
                status=TaskStatus(row["status"]),
                result_data=row["result_json"] or {},
                error_message=row["error_message"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                created_at=row["created_at"],
            )
            for row in rows
        ]


class PostgresArtifactRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
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
                    size_bytes INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cursor.execute(
                "ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT 'user_local_default'"
            )
            connection.commit()

    def create(self, artifact: Artifact) -> Artifact:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO artifacts
                (id, session_id, task_id, owner_user_id, filename, content_type, storage_backend, storage_key, storage_uri, size_bytes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    session_id = EXCLUDED.session_id,
                    task_id = EXCLUDED.task_id,
                    owner_user_id = EXCLUDED.owner_user_id,
                    filename = EXCLUDED.filename,
                    content_type = EXCLUDED.content_type,
                    storage_backend = EXCLUDED.storage_backend,
                    storage_key = EXCLUDED.storage_key,
                    storage_uri = EXCLUDED.storage_uri,
                    size_bytes = EXCLUDED.size_bytes,
                    created_at = EXCLUDED.created_at
                """,
                (
                    artifact.id,
                    artifact.session_id,
                    artifact.task_id,
                    artifact.owner_user_id,
                    artifact.filename,
                    artifact.content_type,
                    artifact.storage_backend,
                    artifact.storage_key,
                    artifact.storage_uri,
                    artifact.size_bytes,
                    artifact.created_at,
                ),
            )
            connection.commit()
        return artifact

    def get(self, artifact_id: str) -> Artifact | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, session_id, task_id, owner_user_id, filename, content_type, storage_backend, storage_key, storage_uri, size_bytes, created_at
                FROM artifacts
                WHERE id = %s
                """,
                (artifact_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return Artifact(
            id=row["id"],
            session_id=row["session_id"],
            task_id=row["task_id"],
            owner_user_id=row["owner_user_id"],
            filename=row["filename"],
            content_type=row["content_type"],
            storage_backend=row["storage_backend"],
            storage_key=row["storage_key"],
            storage_uri=row["storage_uri"],
            size_bytes=row["size_bytes"],
            created_at=row["created_at"],
        )

    def list_by_session(self, session_id: str) -> list[Artifact]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, session_id, task_id, owner_user_id, filename, content_type, storage_backend, storage_key, storage_uri, size_bytes, created_at
                FROM artifacts
                WHERE session_id = %s
                ORDER BY created_at ASC
                """,
                (session_id,),
            )
            rows = cursor.fetchall()
        return [
            Artifact(
                id=row["id"],
                session_id=row["session_id"],
                task_id=row["task_id"],
                owner_user_id=row["owner_user_id"],
                filename=row["filename"],
                content_type=row["content_type"],
                storage_backend=row["storage_backend"],
                storage_key=row["storage_key"],
                storage_uri=row["storage_uri"],
                size_bytes=row["size_bytes"],
                created_at=row["created_at"],
            )
            for row in rows
        ]


class PostgresUploadedFileRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
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
                "ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT 'user_local_default'"
            )
            connection.commit()

    def create(self, uploaded_file: UploadedFile) -> UploadedFile:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO uploaded_files
                (id, session_id, owner_user_id, original_filename, content_type, size_bytes, storage_backend, storage_key, storage_uri, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    session_id = EXCLUDED.session_id,
                    owner_user_id = EXCLUDED.owner_user_id,
                    original_filename = EXCLUDED.original_filename,
                    content_type = EXCLUDED.content_type,
                    size_bytes = EXCLUDED.size_bytes,
                    storage_backend = EXCLUDED.storage_backend,
                    storage_key = EXCLUDED.storage_key,
                    storage_uri = EXCLUDED.storage_uri,
                    created_at = EXCLUDED.created_at
                """,
                (
                    uploaded_file.id,
                    uploaded_file.session_id,
                    uploaded_file.owner_user_id,
                    uploaded_file.original_filename,
                    uploaded_file.content_type,
                    uploaded_file.size_bytes,
                    uploaded_file.storage_backend,
                    uploaded_file.storage_key,
                    uploaded_file.storage_uri,
                    uploaded_file.created_at,
                ),
            )
            connection.commit()
        return uploaded_file

    def get(self, file_id: str) -> UploadedFile | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, session_id, owner_user_id, original_filename, content_type, size_bytes, storage_backend, storage_key, storage_uri, created_at
                FROM uploaded_files
                WHERE id = %s
                """,
                (file_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return UploadedFile(
            id=row["id"],
            session_id=row["session_id"],
            owner_user_id=row["owner_user_id"],
            original_filename=row["original_filename"],
            content_type=row["content_type"],
            size_bytes=row["size_bytes"],
            storage_backend=row["storage_backend"],
            storage_key=row["storage_key"],
            storage_uri=row["storage_uri"],
            created_at=row["created_at"],
        )

    def list_by_session(self, session_id: str) -> list[UploadedFile]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, session_id, owner_user_id, original_filename, content_type, size_bytes, storage_backend, storage_key, storage_uri, created_at
                FROM uploaded_files
                WHERE session_id = %s
                ORDER BY created_at ASC
                """,
                (session_id,),
            )
            rows = cursor.fetchall()

        return [
            UploadedFile(
                id=row["id"],
                session_id=row["session_id"],
                owner_user_id=row["owner_user_id"],
                original_filename=row["original_filename"],
                content_type=row["content_type"],
                size_bytes=row["size_bytes"],
                storage_backend=row["storage_backend"],
                storage_key=row["storage_key"],
                storage_uri=row["storage_uri"],
                created_at=row["created_at"],
            )
            for row in rows
        ]


class PostgresStoredFileRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS stored_files (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    task_id TEXT,
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
                    owner_user_id TEXT NOT NULL DEFAULT 'user_local_default',
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cursor.execute(
                "ALTER TABLE stored_files ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT 'user_local_default'"
            )
            connection.commit()

    def create(self, stored_file: StoredFile) -> StoredFile:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO stored_files
                (id, session_id, task_id, kind, file_type, mime_type, title, original_filename,
                 storage_backend, storage_key, storage_uri, checksum_sha256, size_bytes, is_remote, created_at, updated_at, owner_user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    session_id = EXCLUDED.session_id,
                    task_id = EXCLUDED.task_id,
                    owner_user_id = EXCLUDED.owner_user_id,
                    kind = EXCLUDED.kind,
                    file_type = EXCLUDED.file_type,
                    mime_type = EXCLUDED.mime_type,
                    title = EXCLUDED.title,
                    original_filename = EXCLUDED.original_filename,
                    storage_backend = EXCLUDED.storage_backend,
                    storage_key = EXCLUDED.storage_key,
                    storage_uri = EXCLUDED.storage_uri,
                    checksum_sha256 = EXCLUDED.checksum_sha256,
                    size_bytes = EXCLUDED.size_bytes,
                    is_remote = EXCLUDED.is_remote,
                    created_at = EXCLUDED.created_at,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    stored_file.id,
                    stored_file.session_id,
                    stored_file.task_id,
                    stored_file.kind,
                    stored_file.file_type,
                    stored_file.mime_type,
                    stored_file.title,
                    stored_file.original_filename,
                    stored_file.storage_backend,
                    stored_file.storage_key,
                    stored_file.storage_uri,
                    stored_file.checksum_sha256,
                    stored_file.size_bytes,
                    stored_file.is_remote,
                    stored_file.created_at,
                    stored_file.updated_at,
                    stored_file.owner_user_id,
                ),
            )
            connection.commit()
        return stored_file

    def get(self, stored_file_id: str) -> StoredFile | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM stored_files WHERE id = %s", (stored_file_id,))
            row = cursor.fetchone()
        if row is None:
            return None
        return StoredFile(**row)

    def list_by_session(self, session_id: str) -> list[StoredFile]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM stored_files WHERE session_id = %s ORDER BY created_at ASC", (session_id,))
            rows = cursor.fetchall()
        return [StoredFile(**row) for row in rows]


class PostgresDocumentRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    current_file_id TEXT,
                    document_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.commit()

    def create(self, document: Document) -> Document:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO documents
                (id, session_id, current_file_id, document_type, title, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    session_id = EXCLUDED.session_id,
                    current_file_id = EXCLUDED.current_file_id,
                    document_type = EXCLUDED.document_type,
                    title = EXCLUDED.title,
                    status = EXCLUDED.status,
                    created_at = EXCLUDED.created_at,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    document.id,
                    document.session_id,
                    document.current_file_id,
                    document.document_type,
                    document.title,
                    document.status,
                    document.created_at,
                    document.updated_at,
                ),
            )
            connection.commit()
        return document

    def get(self, document_id: str) -> Document | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM documents WHERE id = %s", (document_id,))
            row = cursor.fetchone()
        if row is None:
            return None
        return Document(**row)

    def list_by_session(self, session_id: str) -> list[Document]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM documents WHERE session_id = %s ORDER BY created_at ASC", (session_id,))
            rows = cursor.fetchall()
        return [Document(**row) for row in rows]


class PostgresDocumentVersionRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS document_versions (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    file_id TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    created_from_task_id TEXT,
                    parent_version_id TEXT,
                    change_summary TEXT,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.commit()

    def create(self, document_version: DocumentVersion) -> DocumentVersion:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO document_versions
                (id, document_id, file_id, version_number, created_from_task_id, parent_version_id, change_summary, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    document_id = EXCLUDED.document_id,
                    file_id = EXCLUDED.file_id,
                    version_number = EXCLUDED.version_number,
                    created_from_task_id = EXCLUDED.created_from_task_id,
                    parent_version_id = EXCLUDED.parent_version_id,
                    change_summary = EXCLUDED.change_summary,
                    created_at = EXCLUDED.created_at
                """,
                (
                    document_version.id,
                    document_version.document_id,
                    document_version.file_id,
                    document_version.version_number,
                    document_version.created_from_task_id,
                    document_version.parent_version_id,
                    document_version.change_summary,
                    document_version.created_at,
                ),
            )
            connection.commit()
        return document_version

    def list_by_document(self, document_id: str) -> list[DocumentVersion]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM document_versions WHERE document_id = %s ORDER BY version_number ASC",
                (document_id,),
            )
            rows = cursor.fetchall()
        return [DocumentVersion(**row) for row in rows]


class PostgresPresentationRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS presentations (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    current_file_id TEXT,
                    presentation_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.commit()

    def create(self, presentation: Presentation) -> Presentation:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO presentations
                (id, session_id, current_file_id, presentation_type, title, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    session_id = EXCLUDED.session_id,
                    current_file_id = EXCLUDED.current_file_id,
                    presentation_type = EXCLUDED.presentation_type,
                    title = EXCLUDED.title,
                    status = EXCLUDED.status,
                    created_at = EXCLUDED.created_at,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    presentation.id,
                    presentation.session_id,
                    presentation.current_file_id,
                    presentation.presentation_type,
                    presentation.title,
                    presentation.status,
                    presentation.created_at,
                    presentation.updated_at,
                ),
            )
            connection.commit()
        return presentation

    def get(self, presentation_id: str) -> Presentation | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM presentations WHERE id = %s", (presentation_id,))
            row = cursor.fetchone()
        if row is None:
            return None
        return Presentation(**row)

    def list_by_session(self, session_id: str) -> list[Presentation]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM presentations WHERE session_id = %s ORDER BY created_at ASC", (session_id,))
            rows = cursor.fetchall()
        return [Presentation(**row) for row in rows]


class PostgresPresentationVersionRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS presentation_versions (
                    id TEXT PRIMARY KEY,
                    presentation_id TEXT NOT NULL,
                    file_id TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    created_from_task_id TEXT,
                    parent_version_id TEXT,
                    change_summary TEXT,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.commit()

    def create(self, presentation_version: PresentationVersion) -> PresentationVersion:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO presentation_versions
                (id, presentation_id, file_id, version_number, created_from_task_id, parent_version_id, change_summary, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    presentation_id = EXCLUDED.presentation_id,
                    file_id = EXCLUDED.file_id,
                    version_number = EXCLUDED.version_number,
                    created_from_task_id = EXCLUDED.created_from_task_id,
                    parent_version_id = EXCLUDED.parent_version_id,
                    change_summary = EXCLUDED.change_summary,
                    created_at = EXCLUDED.created_at
                """,
                (
                    presentation_version.id,
                    presentation_version.presentation_id,
                    presentation_version.file_id,
                    presentation_version.version_number,
                    presentation_version.created_from_task_id,
                    presentation_version.parent_version_id,
                    presentation_version.change_summary,
                    presentation_version.created_at,
                ),
            )
            connection.commit()
        return presentation_version

    def list_by_presentation(self, presentation_id: str) -> list[PresentationVersion]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM presentation_versions WHERE presentation_id = %s ORDER BY version_number ASC",
                (presentation_id,),
            )
            rows = cursor.fetchall()
        return [PresentationVersion(**row) for row in rows]

class PostgresPresentationPlanSnapshotRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS presentation_plan_snapshots (
                    id TEXT PRIMARY KEY,
                    presentation_id TEXT NOT NULL,
                    presentation_version_id TEXT,
                    snapshot_json JSONB NOT NULL,
                    created_from_task_id TEXT,
                    change_summary TEXT,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_presentation_plan_snapshots_presentation "
                "ON presentation_plan_snapshots (presentation_id, created_at)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_presentation_plan_snapshots_version "
                "ON presentation_plan_snapshots (presentation_version_id)"
            )
            connection.commit()

    def create(self, snapshot: PresentationPlanSnapshot) -> PresentationPlanSnapshot:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO presentation_plan_snapshots
                (id, presentation_id, presentation_version_id, snapshot_json, created_from_task_id, change_summary, created_at)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    presentation_id = EXCLUDED.presentation_id,
                    presentation_version_id = EXCLUDED.presentation_version_id,
                    snapshot_json = EXCLUDED.snapshot_json,
                    created_from_task_id = EXCLUDED.created_from_task_id,
                    change_summary = EXCLUDED.change_summary,
                    created_at = EXCLUDED.created_at
                """,
                (
                    snapshot.id,
                    snapshot.presentation_id,
                    snapshot.presentation_version_id,
                    json.dumps(snapshot.snapshot_json),
                    snapshot.created_from_task_id,
                    snapshot.change_summary,
                    snapshot.created_at,
                ),
            )
            connection.commit()
        return snapshot

    def get(self, snapshot_id: str) -> PresentationPlanSnapshot | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, presentation_id, presentation_version_id, snapshot_json, created_from_task_id, change_summary, created_at
                FROM presentation_plan_snapshots
                WHERE id = %s
                """,
                (snapshot_id,),
            )
            row = cursor.fetchone()
        return self._row_to_snapshot(row)

    def list_by_presentation(self, presentation_id: str) -> list[PresentationPlanSnapshot]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, presentation_id, presentation_version_id, snapshot_json, created_from_task_id, change_summary, created_at
                FROM presentation_plan_snapshots
                WHERE presentation_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (presentation_id,),
            )
            rows = cursor.fetchall()
        return [snapshot for row in rows if (snapshot := self._row_to_snapshot(row)) is not None]

    def get_latest_for_presentation(self, presentation_id: str) -> PresentationPlanSnapshot | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, presentation_id, presentation_version_id, snapshot_json, created_from_task_id, change_summary, created_at
                FROM presentation_plan_snapshots
                WHERE presentation_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (presentation_id,),
            )
            row = cursor.fetchone()
        return self._row_to_snapshot(row)

    def get_by_version(self, presentation_version_id: str) -> PresentationPlanSnapshot | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, presentation_id, presentation_version_id, snapshot_json, created_from_task_id, change_summary, created_at
                FROM presentation_plan_snapshots
                WHERE presentation_version_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (presentation_version_id,),
            )
            row = cursor.fetchone()
        return self._row_to_snapshot(row)

    @staticmethod
    def _row_to_snapshot(row: dict[str, object] | None) -> PresentationPlanSnapshot | None:
        if row is None:
            return None
        snapshot_json = row["snapshot_json"]
        if isinstance(snapshot_json, str):
            snapshot_json = json.loads(snapshot_json)
        return PresentationPlanSnapshot(
            id=row["id"],
            presentation_id=row["presentation_id"],
            presentation_version_id=row["presentation_version_id"],
            snapshot_json=snapshot_json,
            created_from_task_id=row["created_from_task_id"],
            change_summary=row["change_summary"],
            created_at=row["created_at"],
        )




class PostgresArtifactSourceRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS artifact_sources (
                    id TEXT PRIMARY KEY,
                    artifact_id TEXT NOT NULL,
                    source_file_id TEXT,
                    source_document_id TEXT,
                    source_presentation_id TEXT,
                    role TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.commit()

    def create(self, artifact_source: ArtifactSource) -> ArtifactSource:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO artifact_sources
                (id, artifact_id, source_file_id, source_document_id, source_presentation_id, role, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    artifact_id = EXCLUDED.artifact_id,
                    source_file_id = EXCLUDED.source_file_id,
                    source_document_id = EXCLUDED.source_document_id,
                    source_presentation_id = EXCLUDED.source_presentation_id,
                    role = EXCLUDED.role,
                    created_at = EXCLUDED.created_at
                """,
                (
                    artifact_source.id,
                    artifact_source.artifact_id,
                    artifact_source.source_file_id,
                    artifact_source.source_document_id,
                    artifact_source.source_presentation_id,
                    artifact_source.role,
                    artifact_source.created_at,
                ),
            )
            connection.commit()
        return artifact_source

    def list_by_artifact(self, artifact_id: str) -> list[ArtifactSource]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM artifact_sources WHERE artifact_id = %s ORDER BY created_at ASC", (artifact_id,))
            rows = cursor.fetchall()
        return [ArtifactSource(**row) for row in rows]


class PostgresDerivedContentRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS derived_contents (
                    id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    content_kind TEXT NOT NULL,
                    text_content TEXT,
                    structured_json JSONB,
                    outline_json JSONB,
                    language TEXT,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.commit()

    def create(self, derived_content: DerivedContent) -> DerivedContent:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO derived_contents
                (id, file_id, content_kind, text_content, structured_json, outline_json, language, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    file_id = EXCLUDED.file_id,
                    content_kind = EXCLUDED.content_kind,
                    text_content = EXCLUDED.text_content,
                    structured_json = EXCLUDED.structured_json,
                    outline_json = EXCLUDED.outline_json,
                    language = EXCLUDED.language,
                    created_at = EXCLUDED.created_at,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    derived_content.id,
                    derived_content.file_id,
                    derived_content.content_kind,
                    derived_content.text_content,
                    json.dumps(derived_content.structured_json) if derived_content.structured_json is not None else None,
                    json.dumps(derived_content.outline_json) if derived_content.outline_json is not None else None,
                    derived_content.language,
                    derived_content.created_at,
                    derived_content.updated_at,
                ),
            )
            connection.commit()
        return derived_content

    def list_by_file(self, file_id: str) -> list[DerivedContent]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM derived_contents WHERE file_id = %s ORDER BY created_at ASC", (file_id,))
            rows = cursor.fetchall()
        return [DerivedContent(**row) for row in rows]
