from __future__ import annotations

import json
from datetime import datetime
from threading import Lock
from typing import Any

from backend.app.domain import Artifact, Session, Task, TaskStatus, TaskType, UploadedFile


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


class PostgresSessionRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
        connection.commit()

    def create(self, session: Session) -> Session:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sessions (id, created_at)
                VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE SET created_at = EXCLUDED.created_at
                """,
                (session.id, session.created_at),
            )
            connection.commit()
        return session

    def get(self, session_id: str) -> Session | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT id, created_at FROM sessions WHERE id = %s", (session_id,))
            row = cursor.fetchone()
        if row is None:
            return None
        return Session(id=row["id"], created_at=_parse_datetime(row["created_at"]))


class PostgresTaskRepository(_PostgresRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
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
            connection.commit()

    def create(self, task: Task) -> Task:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks
                (id, session_id, task_type, status, result_json, error_message, started_at, completed_at, created_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    session_id = EXCLUDED.session_id,
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
                SELECT id, session_id, task_type, status, result_json, error_message, started_at, completed_at, created_at
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
                SELECT id, session_id, task_type, status, result_json, error_message, started_at, completed_at, created_at
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
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    storage_path TEXT NOT NULL DEFAULT '',
                    size_bytes INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.commit()

    def create(self, artifact: Artifact) -> Artifact:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO artifacts
                (id, session_id, task_id, filename, content_type, storage_path, size_bytes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    session_id = EXCLUDED.session_id,
                    task_id = EXCLUDED.task_id,
                    filename = EXCLUDED.filename,
                    content_type = EXCLUDED.content_type,
                    storage_path = EXCLUDED.storage_path,
                    size_bytes = EXCLUDED.size_bytes,
                    created_at = EXCLUDED.created_at
                """,
                (
                    artifact.id,
                    artifact.session_id,
                    artifact.task_id,
                    artifact.filename,
                    artifact.content_type,
                    artifact.storage_path,
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
                SELECT id, session_id, task_id, filename, content_type, storage_path, size_bytes, created_at
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
            filename=row["filename"],
            content_type=row["content_type"],
            storage_path=row["storage_path"],
            size_bytes=row["size_bytes"],
            created_at=row["created_at"],
        )

    def list_by_session(self, session_id: str) -> list[Artifact]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, session_id, task_id, filename, content_type, storage_path, size_bytes, created_at
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
                filename=row["filename"],
                content_type=row["content_type"],
                storage_path=row["storage_path"],
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
                    original_filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.commit()

    def create(self, uploaded_file: UploadedFile) -> UploadedFile:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO uploaded_files
                (id, session_id, original_filename, content_type, size_bytes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    session_id = EXCLUDED.session_id,
                    original_filename = EXCLUDED.original_filename,
                    content_type = EXCLUDED.content_type,
                    size_bytes = EXCLUDED.size_bytes,
                    created_at = EXCLUDED.created_at
                """,
                (
                    uploaded_file.id,
                    uploaded_file.session_id,
                    uploaded_file.original_filename,
                    uploaded_file.content_type,
                    uploaded_file.size_bytes,
                    uploaded_file.created_at,
                ),
            )
            connection.commit()
        return uploaded_file

    def get(self, file_id: str) -> UploadedFile | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, session_id, original_filename, content_type, size_bytes, created_at
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
            original_filename=row["original_filename"],
            content_type=row["content_type"],
            size_bytes=row["size_bytes"],
            created_at=row["created_at"],
        )

    def list_by_session(self, session_id: str) -> list[UploadedFile]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, session_id, original_filename, content_type, size_bytes, created_at
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
                original_filename=row["original_filename"],
                content_type=row["content_type"],
                size_bytes=row["size_bytes"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
