from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock

from backend.app.domain import (
    Artifact,
    ArtifactSource,
    DerivedContent,
    Document,
    Presentation,
    Session,
    StoredFile,
    Task,
    TaskStatus,
    TaskType,
    UploadedFile,
    User,
)


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


class _SqliteRepositoryBase:
    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_schema(self) -> None:
        raise NotImplementedError

    @staticmethod
    def _ensure_column(*, connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        existing_columns = {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


class SqliteUserRepository(_SqliteRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    display_name TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    is_superuser INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, user: User) -> User:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO users
                (id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    user.email,
                    user.password_hash,
                    user.display_name,
                    1 if user.is_active else 0,
                    1 if user.is_superuser else 0,
                    user.created_at.isoformat(),
                    user.updated_at.isoformat(),
                ),
            )
        return user

    def get(self, user_id: str) -> User | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return User(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            display_name=row["display_name"],
            is_active=bool(row["is_active"]),
            is_superuser=bool(row["is_superuser"]),
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def get_by_email(self, email: str) -> User | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at
                FROM users
                WHERE email = ?
                """,
                (email.strip().lower(),),
            ).fetchone()
        if row is None:
            return None
        return User(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            display_name=row["display_name"],
            is_active=bool(row["is_active"]),
            is_superuser=bool(row["is_superuser"]),
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def list(self) -> list[User]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at
                FROM users
                ORDER BY created_at ASC
                """
            ).fetchall()
        return [
            User(
                id=row["id"],
                email=row["email"],
                password_hash=row["password_hash"],
                display_name=row["display_name"],
                is_active=bool(row["is_active"]),
                is_superuser=bool(row["is_superuser"]),
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]


class SqliteSessionRepository(_SqliteRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    owner_user_id TEXT NOT NULL DEFAULT 'user_local_default'
                )
                """
            )
            self._ensure_column(
                connection=connection,
                table="sessions",
                column="owner_user_id",
                definition="TEXT NOT NULL DEFAULT 'user_local_default'",
            )

    def create(self, session: Session) -> Session:
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO sessions (id, created_at, owner_user_id) VALUES (?, ?, ?)",
                (session.id, session.created_at.isoformat(), session.owner_user_id),
            )
        return session

    def get(self, session_id: str) -> Session | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, created_at, owner_user_id FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return Session(
            id=row["id"],
            created_at=_parse_datetime(row["created_at"]),
            owner_user_id=row["owner_user_id"],
        )


class SqliteTaskRepository(_SqliteRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    owner_user_id TEXT NOT NULL DEFAULT 'user_local_default',
                    status TEXT NOT NULL,
                    result_json TEXT NOT NULL DEFAULT '{}',
                    error_message TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._ensure_column(
                connection=connection,
                table="tasks",
                column="owner_user_id",
                definition="TEXT NOT NULL DEFAULT 'user_local_default'",
            )
            self._ensure_column(connection=connection, table="tasks", column="result_json", definition="TEXT NOT NULL DEFAULT '{}'")
            self._ensure_column(connection=connection, table="tasks", column="error_message", definition="TEXT")
            self._ensure_column(connection=connection, table="tasks", column="started_at", definition="TEXT")
            self._ensure_column(connection=connection, table="tasks", column="completed_at", definition="TEXT")

    def create(self, task: Task) -> Task:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO tasks
                (id, session_id, task_type, owner_user_id, status, result_json, error_message, started_at, completed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    task.session_id,
                    task.task_type.value,
                    task.owner_user_id,
                    task.status.value,
                    json.dumps(task.result_data),
                    task.error_message,
                    task.started_at.isoformat() if task.started_at else None,
                    task.completed_at.isoformat() if task.completed_at else None,
                    task.created_at.isoformat(),
                ),
            )
        return task

    def update(self, task: Task) -> Task:
        return self.create(task)

    def get(self, task_id: str) -> Task | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, session_id, task_type, owner_user_id, status, result_json, error_message, started_at, completed_at, created_at
                FROM tasks
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return Task(
            id=row["id"],
            session_id=row["session_id"],
            task_type=TaskType(row["task_type"]),
            owner_user_id=row["owner_user_id"],
            status=TaskStatus(row["status"]),
            result_data=json.loads(row["result_json"] or "{}"),
            error_message=row["error_message"],
            started_at=_parse_datetime(row["started_at"]) if row["started_at"] else None,
            completed_at=_parse_datetime(row["completed_at"]) if row["completed_at"] else None,
            created_at=_parse_datetime(row["created_at"]),
        )

    def list_by_session(self, session_id: str) -> list[Task]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, task_type, owner_user_id, status, result_json, error_message, started_at, completed_at, created_at
                FROM tasks
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
        return [
            Task(
                id=row["id"],
                session_id=row["session_id"],
                task_type=TaskType(row["task_type"]),
                owner_user_id=row["owner_user_id"],
                status=TaskStatus(row["status"]),
                result_data=json.loads(row["result_json"] or "{}"),
                error_message=row["error_message"],
                started_at=_parse_datetime(row["started_at"]) if row["started_at"] else None,
                completed_at=_parse_datetime(row["completed_at"]) if row["completed_at"] else None,
                created_at=_parse_datetime(row["created_at"]),
            )
            for row in rows
        ]


class SqliteArtifactRepository(_SqliteRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    owner_user_id TEXT NOT NULL DEFAULT 'user_local_default',
                    storage_backend TEXT NOT NULL DEFAULT 'local',
                    storage_key TEXT NOT NULL DEFAULT '',
                    storage_uri TEXT NOT NULL DEFAULT '',
                    size_bytes INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._ensure_column(connection=connection, table="artifacts", column="owner_user_id", definition="TEXT NOT NULL DEFAULT 'user_local_default'")
            self._ensure_column(connection=connection, table="artifacts", column="storage_backend", definition="TEXT NOT NULL DEFAULT 'local'")
            self._ensure_column(connection=connection, table="artifacts", column="storage_key", definition="TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection=connection, table="artifacts", column="storage_uri", definition="TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection=connection, table="artifacts", column="size_bytes", definition="INTEGER NOT NULL DEFAULT 0")

    def create(self, artifact: Artifact) -> Artifact:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO artifacts
                (id, session_id, task_id, filename, content_type, owner_user_id, storage_backend, storage_key, storage_uri, size_bytes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact.id,
                    artifact.session_id,
                    artifact.task_id,
                    artifact.filename,
                    artifact.content_type,
                    artifact.owner_user_id,
                    artifact.storage_backend,
                    artifact.storage_key,
                    artifact.storage_uri,
                    artifact.size_bytes,
                    artifact.created_at.isoformat(),
                ),
            )
        return artifact

    def get(self, artifact_id: str) -> Artifact | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, session_id, task_id, filename, content_type, owner_user_id, storage_backend, storage_key, storage_uri, size_bytes, created_at
                FROM artifacts
                WHERE id = ?
                """,
                (artifact_id,),
            ).fetchone()
        if row is None:
            return None
        return Artifact(
            id=row["id"],
            session_id=row["session_id"],
            task_id=row["task_id"],
            filename=row["filename"],
            content_type=row["content_type"],
            owner_user_id=row["owner_user_id"],
            storage_backend=row["storage_backend"],
            storage_key=row["storage_key"],
            storage_uri=row["storage_uri"],
            size_bytes=row["size_bytes"],
            created_at=_parse_datetime(row["created_at"]),
        )

    def list_by_session(self, session_id: str) -> list[Artifact]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, task_id, filename, content_type, owner_user_id, storage_backend, storage_key, storage_uri, size_bytes, created_at
                FROM artifacts
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
        return [
            Artifact(
                id=row["id"],
                session_id=row["session_id"],
                task_id=row["task_id"],
                filename=row["filename"],
                content_type=row["content_type"],
                owner_user_id=row["owner_user_id"],
                storage_backend=row["storage_backend"],
                storage_key=row["storage_key"],
                storage_uri=row["storage_uri"],
                size_bytes=row["size_bytes"],
                created_at=_parse_datetime(row["created_at"]),
            )
            for row in rows
        ]


class SqliteUploadedFileRepository(_SqliteRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    owner_user_id TEXT NOT NULL DEFAULT 'user_local_default',
                    storage_backend TEXT NOT NULL DEFAULT 'local',
                    storage_key TEXT NOT NULL DEFAULT '',
                    storage_uri TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            self._ensure_column(connection=connection, table="uploaded_files", column="owner_user_id", definition="TEXT NOT NULL DEFAULT 'user_local_default'")
            self._ensure_column(connection=connection, table="uploaded_files", column="storage_backend", definition="TEXT NOT NULL DEFAULT 'local'")
            self._ensure_column(connection=connection, table="uploaded_files", column="storage_key", definition="TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection=connection, table="uploaded_files", column="storage_uri", definition="TEXT NOT NULL DEFAULT ''")

    def create(self, uploaded_file: UploadedFile) -> UploadedFile:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO uploaded_files
                (id, session_id, original_filename, content_type, size_bytes, owner_user_id, storage_backend, storage_key, storage_uri, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uploaded_file.id,
                    uploaded_file.session_id,
                    uploaded_file.original_filename,
                    uploaded_file.content_type,
                    uploaded_file.size_bytes,
                    uploaded_file.owner_user_id,
                    uploaded_file.storage_backend,
                    uploaded_file.storage_key,
                    uploaded_file.storage_uri,
                    uploaded_file.created_at.isoformat(),
                ),
            )
        return uploaded_file

    def get(self, file_id: str) -> UploadedFile | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, session_id, original_filename, content_type, size_bytes, owner_user_id, storage_backend, storage_key, storage_uri, created_at
                FROM uploaded_files
                WHERE id = ?
                """,
                (file_id,),
            ).fetchone()
        if row is None:
            return None
        return UploadedFile(
            id=row["id"],
            session_id=row["session_id"],
            original_filename=row["original_filename"],
            content_type=row["content_type"],
            size_bytes=row["size_bytes"],
            owner_user_id=row["owner_user_id"],
            storage_backend=row["storage_backend"],
            storage_key=row["storage_key"],
            storage_uri=row["storage_uri"],
            created_at=_parse_datetime(row["created_at"]),
        )

    def list_by_session(self, session_id: str) -> list[UploadedFile]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, original_filename, content_type, size_bytes, owner_user_id, storage_backend, storage_key, storage_uri, created_at
                FROM uploaded_files
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
        return [
            UploadedFile(
                id=row["id"],
                session_id=row["session_id"],
                original_filename=row["original_filename"],
                content_type=row["content_type"],
                size_bytes=row["size_bytes"],
                owner_user_id=row["owner_user_id"],
                storage_backend=row["storage_backend"],
                storage_key=row["storage_key"],
                storage_uri=row["storage_uri"],
                created_at=_parse_datetime(row["created_at"]),
            )
            for row in rows
        ]


class SqliteStoredFileRepository(_SqliteRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
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
                    size_bytes INTEGER,
                    is_remote INTEGER NOT NULL DEFAULT 0,
                    owner_user_id TEXT NOT NULL DEFAULT 'user_local_default',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._ensure_column(connection=connection, table="stored_files", column="owner_user_id", definition="TEXT NOT NULL DEFAULT 'user_local_default'")

    def create(self, stored_file: StoredFile) -> StoredFile:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO stored_files
                (id, session_id, task_id, kind, file_type, mime_type, title, original_filename,
                 storage_backend, storage_key, storage_uri, checksum_sha256, size_bytes, is_remote, owner_user_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    1 if stored_file.is_remote else 0,
                    stored_file.owner_user_id,
                    stored_file.created_at.isoformat(),
                    stored_file.updated_at.isoformat(),
                ),
            )
        return stored_file

    def get(self, stored_file_id: str) -> StoredFile | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM stored_files WHERE id = ?", (stored_file_id,)).fetchone()
        if row is None:
            return None
        return StoredFile(
            id=row["id"],
            session_id=row["session_id"],
            task_id=row["task_id"],
            kind=row["kind"],
            file_type=row["file_type"],
            mime_type=row["mime_type"],
            title=row["title"],
            original_filename=row["original_filename"],
            storage_backend=row["storage_backend"],
            storage_key=row["storage_key"],
            storage_uri=row["storage_uri"],
            checksum_sha256=row["checksum_sha256"],
            size_bytes=row["size_bytes"],
            is_remote=bool(row["is_remote"]),
            owner_user_id=row["owner_user_id"],
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def list_by_session(self, session_id: str) -> list[StoredFile]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM stored_files WHERE session_id = ? ORDER BY created_at ASC", (session_id,)).fetchall()
        return [
            StoredFile(
                id=row["id"],
                session_id=row["session_id"],
                task_id=row["task_id"],
                kind=row["kind"],
                file_type=row["file_type"],
                mime_type=row["mime_type"],
                title=row["title"],
                original_filename=row["original_filename"],
                storage_backend=row["storage_backend"],
                storage_key=row["storage_key"],
                storage_uri=row["storage_uri"],
                checksum_sha256=row["checksum_sha256"],
                size_bytes=row["size_bytes"],
                is_remote=bool(row["is_remote"]),
                owner_user_id=row["owner_user_id"],
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]


class SqliteDocumentRepository(_SqliteRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    current_file_id TEXT,
                    document_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, document: Document) -> Document:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO documents
                (id, session_id, current_file_id, document_type, title, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.session_id,
                    document.current_file_id,
                    document.document_type,
                    document.title,
                    document.status,
                    document.created_at.isoformat(),
                    document.updated_at.isoformat(),
                ),
            )
        return document

    def get(self, document_id: str) -> Document | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        if row is None:
            return None
        return Document(
            id=row["id"],
            session_id=row["session_id"],
            current_file_id=row["current_file_id"],
            document_type=row["document_type"],
            title=row["title"],
            status=row["status"],
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def list_by_session(self, session_id: str) -> list[Document]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM documents WHERE session_id = ? ORDER BY created_at ASC", (session_id,)).fetchall()
        return [
            Document(
                id=row["id"],
                session_id=row["session_id"],
                current_file_id=row["current_file_id"],
                document_type=row["document_type"],
                title=row["title"],
                status=row["status"],
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]


class SqlitePresentationRepository(_SqliteRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS presentations (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    current_file_id TEXT,
                    presentation_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, presentation: Presentation) -> Presentation:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO presentations
                (id, session_id, current_file_id, presentation_type, title, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    presentation.id,
                    presentation.session_id,
                    presentation.current_file_id,
                    presentation.presentation_type,
                    presentation.title,
                    presentation.status,
                    presentation.created_at.isoformat(),
                    presentation.updated_at.isoformat(),
                ),
            )
        return presentation

    def get(self, presentation_id: str) -> Presentation | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM presentations WHERE id = ?", (presentation_id,)).fetchone()
        if row is None:
            return None
        return Presentation(
            id=row["id"],
            session_id=row["session_id"],
            current_file_id=row["current_file_id"],
            presentation_type=row["presentation_type"],
            title=row["title"],
            status=row["status"],
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def list_by_session(self, session_id: str) -> list[Presentation]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM presentations WHERE session_id = ? ORDER BY created_at ASC", (session_id,)).fetchall()
        return [
            Presentation(
                id=row["id"],
                session_id=row["session_id"],
                current_file_id=row["current_file_id"],
                presentation_type=row["presentation_type"],
                title=row["title"],
                status=row["status"],
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]


class SqliteArtifactSourceRepository(_SqliteRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS artifact_sources (
                    id TEXT PRIMARY KEY,
                    artifact_id TEXT NOT NULL,
                    source_file_id TEXT,
                    source_document_id TEXT,
                    source_presentation_id TEXT,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def create(self, artifact_source: ArtifactSource) -> ArtifactSource:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO artifact_sources
                (id, artifact_id, source_file_id, source_document_id, source_presentation_id, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_source.id,
                    artifact_source.artifact_id,
                    artifact_source.source_file_id,
                    artifact_source.source_document_id,
                    artifact_source.source_presentation_id,
                    artifact_source.role,
                    artifact_source.created_at.isoformat(),
                ),
            )
        return artifact_source

    def list_by_artifact(self, artifact_id: str) -> list[ArtifactSource]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM artifact_sources WHERE artifact_id = ? ORDER BY created_at ASC", (artifact_id,)).fetchall()
        return [
            ArtifactSource(
                id=row["id"],
                artifact_id=row["artifact_id"],
                source_file_id=row["source_file_id"],
                source_document_id=row["source_document_id"],
                source_presentation_id=row["source_presentation_id"],
                role=row["role"],
                created_at=_parse_datetime(row["created_at"]),
            )
            for row in rows
        ]


class SqliteDerivedContentRepository(_SqliteRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS derived_contents (
                    id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    content_kind TEXT NOT NULL,
                    text_content TEXT,
                    structured_json TEXT,
                    outline_json TEXT,
                    language TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, derived_content: DerivedContent) -> DerivedContent:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO derived_contents
                (id, file_id, content_kind, text_content, structured_json, outline_json, language, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    derived_content.id,
                    derived_content.file_id,
                    derived_content.content_kind,
                    derived_content.text_content,
                    json.dumps(derived_content.structured_json) if derived_content.structured_json is not None else None,
                    json.dumps(derived_content.outline_json) if derived_content.outline_json is not None else None,
                    derived_content.language,
                    derived_content.created_at.isoformat(),
                    derived_content.updated_at.isoformat(),
                ),
            )
        return derived_content

    def list_by_file(self, file_id: str) -> list[DerivedContent]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM derived_contents WHERE file_id = ? ORDER BY created_at ASC", (file_id,)).fetchall()
        return [
            DerivedContent(
                id=row["id"],
                file_id=row["file_id"],
                content_kind=row["content_kind"],
                text_content=row["text_content"],
                structured_json=json.loads(row["structured_json"]) if row["structured_json"] else None,
                outline_json=json.loads(row["outline_json"]) if row["outline_json"] else None,
                language=row["language"],
                created_at=_parse_datetime(row["created_at"]),
                updated_at=_parse_datetime(row["updated_at"]),
            )
            for row in rows
        ]
