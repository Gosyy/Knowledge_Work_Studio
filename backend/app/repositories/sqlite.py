from __future__ import annotations

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from threading import Lock

from backend.app.domain import Artifact, Session, Task, TaskStatus, TaskType, UploadedFile


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


class SqliteSessionRepository(_SqliteRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL
                )
                """
            )

    def create(self, session: Session) -> Session:
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO sessions (id, created_at) VALUES (?, ?)",
                (session.id, session.created_at.isoformat()),
            )
        return session

    def get(self, session_id: str) -> Session | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, created_at FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return Session(id=row["id"], created_at=_parse_datetime(row["created_at"]))


class SqliteTaskRepository(_SqliteRepositoryBase):
    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
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
                column="result_json",
                definition="TEXT NOT NULL DEFAULT '{}'",
            )
            self._ensure_column(
                connection=connection,
                table="tasks",
                column="error_message",
                definition="TEXT",
            )
            self._ensure_column(
                connection=connection,
                table="tasks",
                column="started_at",
                definition="TEXT",
            )
            self._ensure_column(
                connection=connection,
                table="tasks",
                column="completed_at",
                definition="TEXT",
            )

    @staticmethod
    def _ensure_column(*, connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        existing_columns = {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def create(self, task: Task) -> Task:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO tasks
                (id, session_id, task_type, status, result_json, error_message, started_at, completed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    task.session_id,
                    task.task_type.value,
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
                SELECT id, session_id, task_type, status, result_json, error_message, started_at, completed_at, created_at
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
                SELECT id, session_id, task_type, status, result_json, error_message, started_at, completed_at, created_at
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
                    storage_backend TEXT NOT NULL DEFAULT 'local',
                    storage_key TEXT NOT NULL DEFAULT '',
                    storage_uri TEXT NOT NULL DEFAULT '',
                    size_bytes INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._ensure_column(
                connection=connection,
                table="artifacts",
                column="storage_backend",
                definition="TEXT NOT NULL DEFAULT 'local'",
            )
            self._ensure_column(
                connection=connection,
                table="artifacts",
                column="storage_key",
                definition="TEXT NOT NULL DEFAULT ''",
            )
            self._ensure_column(
                connection=connection,
                table="artifacts",
                column="storage_uri",
                definition="TEXT NOT NULL DEFAULT ''",
            )
            self._ensure_column(
                connection=connection,
                table="artifacts",
                column="size_bytes",
                definition="INTEGER NOT NULL DEFAULT 0",
            )

    @staticmethod
    def _ensure_column(*, connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        existing_columns = {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def create(self, artifact: Artifact) -> Artifact:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO artifacts
                (id, session_id, task_id, filename, content_type, storage_backend, storage_key, storage_uri, size_bytes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact.id,
                    artifact.session_id,
                    artifact.task_id,
                    artifact.filename,
                    artifact.content_type,
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
                SELECT id, session_id, task_id, filename, content_type, storage_backend, storage_key, storage_uri, size_bytes, created_at
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
                SELECT id, session_id, task_id, filename, content_type, storage_backend, storage_key, storage_uri, size_bytes, created_at
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
                storage_backend=row["storage_backend"],
                storage_key=row["storage_key"],
                storage_uri=row["storage_uri"],
                size_bytes=row["size_bytes"],
                created_at=_parse_datetime(row["created_at"]),
            )
            for row in rows
        ]


class SqliteUploadedFileRepository(_SqliteRepositoryBase):
    @staticmethod
    def _ensure_column(*, connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        existing_columns = {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

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
                    storage_backend TEXT NOT NULL DEFAULT 'local',
                    storage_key TEXT NOT NULL DEFAULT '',
                    storage_uri TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            self._ensure_column(
                connection=connection,
                table="uploaded_files",
                column="storage_backend",
                definition="TEXT NOT NULL DEFAULT 'local'",
            )
            self._ensure_column(
                connection=connection,
                table="uploaded_files",
                column="storage_key",
                definition="TEXT NOT NULL DEFAULT ''",
            )
            self._ensure_column(
                connection=connection,
                table="uploaded_files",
                column="storage_uri",
                definition="TEXT NOT NULL DEFAULT ''",
            )

    def create(self, uploaded_file: UploadedFile) -> UploadedFile:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO uploaded_files
                (id, session_id, original_filename, content_type, size_bytes, storage_backend, storage_key, storage_uri, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uploaded_file.id,
                    uploaded_file.session_id,
                    uploaded_file.original_filename,
                    uploaded_file.content_type,
                    uploaded_file.size_bytes,
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
                SELECT id, session_id, original_filename, content_type, size_bytes, storage_backend, storage_key, storage_uri, created_at
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
            storage_backend=row["storage_backend"],
            storage_key=row["storage_key"],
            storage_uri=row["storage_uri"],
            created_at=_parse_datetime(row["created_at"]),
        )

    def list_by_session(self, session_id: str) -> list[UploadedFile]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, original_filename, content_type, size_bytes, storage_backend, storage_key, storage_uri, created_at
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
                storage_backend=row["storage_backend"],
                storage_key=row["storage_key"],
                storage_uri=row["storage_uri"],
                created_at=_parse_datetime(row["created_at"]),
            )
            for row in rows
        ]
