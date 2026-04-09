from __future__ import annotations

import json
from datetime import datetime

from backend.app.domain import Artifact, Session, Task, TaskStatus, TaskType, UploadedFile
from backend.app.integrations.database import SQLiteDatabase


class SQLiteSessionRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def create(self, session: Session) -> Session:
        with self._database.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO sessions (id, created_at) VALUES (?, ?)",
                (session.id, session.created_at.isoformat()),
            )
            connection.commit()
        return session

    def get(self, session_id: str) -> Session | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT id, created_at FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return Session(id=row["id"], created_at=datetime.fromisoformat(row["created_at"]))


class SQLiteTaskRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def create(self, task: Task) -> Task:
        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO tasks (id, session_id, task_type, status, result_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    task.session_id,
                    task.task_type.value,
                    task.status.value,
                    json.dumps(task.result_data) if task.result_data is not None else None,
                    task.created_at.isoformat(),
                ),
            )
            connection.commit()
        return task

    def update(self, task: Task) -> Task:
        return self.create(task)

    def get(self, task_id: str) -> Task | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT id, session_id, task_type, status, result_json, created_at FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return _task_from_row(row)

    def list_by_session(self, session_id: str) -> list[Task]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, task_type, status, result_json, created_at
                FROM tasks
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
        return [_task_from_row(row) for row in rows]


class SQLiteArtifactRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def create(self, artifact: Artifact) -> Artifact:
        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO artifacts (
                    id,
                    session_id,
                    task_id,
                    filename,
                    content_type,
                    storage_path,
                    size_bytes,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact.id,
                    artifact.session_id,
                    artifact.task_id,
                    artifact.filename,
                    artifact.content_type,
                    artifact.storage_path,
                    artifact.size_bytes,
                    artifact.created_at.isoformat(),
                ),
            )
            connection.commit()
        return artifact

    def get(self, artifact_id: str) -> Artifact | None:
        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, session_id, task_id, filename, content_type, storage_path, size_bytes, created_at
                FROM artifacts
                WHERE id = ?
                """,
                (artifact_id,),
            ).fetchone()
        if row is None:
            return None
        return _artifact_from_row(row)

    def list_by_session(self, session_id: str) -> list[Artifact]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, task_id, filename, content_type, storage_path, size_bytes, created_at
                FROM artifacts
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
        return [_artifact_from_row(row) for row in rows]


class SQLiteUploadedFileRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def create(self, uploaded_file: UploadedFile) -> UploadedFile:
        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO uploaded_files (
                    id,
                    session_id,
                    original_filename,
                    content_type,
                    size_bytes,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    uploaded_file.id,
                    uploaded_file.session_id,
                    uploaded_file.original_filename,
                    uploaded_file.content_type,
                    uploaded_file.size_bytes,
                    uploaded_file.created_at.isoformat(),
                ),
            )
            connection.commit()
        return uploaded_file

    def get(self, file_id: str) -> UploadedFile | None:
        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, session_id, original_filename, content_type, size_bytes, created_at
                FROM uploaded_files
                WHERE id = ?
                """,
                (file_id,),
            ).fetchone()
        if row is None:
            return None
        return _uploaded_file_from_row(row)

    def list_by_session(self, session_id: str) -> list[UploadedFile]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, session_id, original_filename, content_type, size_bytes, created_at
                FROM uploaded_files
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
        return [_uploaded_file_from_row(row) for row in rows]


def _task_from_row(row: dict[str, object]) -> Task:
    return Task(
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        task_type=TaskType(str(row["task_type"])),
        status=TaskStatus(str(row["status"])),
        result_data=json.loads(str(row["result_json"])) if row["result_json"] is not None else None,
        created_at=datetime.fromisoformat(str(row["created_at"])),
    )


def _artifact_from_row(row: dict[str, object]) -> Artifact:
    return Artifact(
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        task_id=str(row["task_id"]),
        filename=str(row["filename"]),
        content_type=str(row["content_type"]),
        storage_path=str(row["storage_path"]) if row["storage_path"] is not None else None,
        size_bytes=int(row["size_bytes"]) if row["size_bytes"] is not None else None,
        created_at=datetime.fromisoformat(str(row["created_at"])),
    )


def _uploaded_file_from_row(row: dict[str, object]) -> UploadedFile:
    return UploadedFile(
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        original_filename=str(row["original_filename"]),
        content_type=str(row["content_type"]),
        size_bytes=int(row["size_bytes"]),
        created_at=datetime.fromisoformat(str(row["created_at"])),
    )
