from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from backend.app.domain import Session, StoredFile, Task, TaskStatus, TaskType, UploadedFile
from backend.app.integrations.storage import upload_storage_key
from backend.app.repositories import (
    FileStorage,
    SessionRepository,
    StoredFileRepository,
    TaskRepository,
    UploadedFileRepository,
)


def _infer_file_type(*, original_filename: str, content_type: str) -> str:
    suffix = Path(original_filename).suffix.lower().lstrip(".")
    if suffix:
        return suffix
    if "/" in content_type:
        return content_type.rsplit("/", 1)[-1].lower()
    return "bin"


@dataclass
class SessionTaskService:
    sessions: SessionRepository
    tasks: TaskRepository
    uploads: UploadedFileRepository
    storage: FileStorage
    stored_files: StoredFileRepository | None = None

    def create_session(self) -> Session:
        session = Session(id=f"ses_{uuid4().hex}")
        return self.sessions.create(session)

    def get_session(self, session_id: str) -> Session:
        session = self.sessions.get(session_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return session

    def create_task(self, session_id: str, task_type: TaskType) -> Task:
        self.get_session(session_id)
        task = Task(id=f"task_{uuid4().hex}", session_id=session_id, task_type=task_type, status=TaskStatus.PENDING)
        return self.tasks.create(task)

    def get_task(self, task_id: str) -> Task:
        task = self.tasks.get(task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return task

    def mark_task_running(self, task_id: str) -> Task:
        task = self.get_task(task_id)
        updated = Task(
            id=task.id,
            session_id=task.session_id,
            task_type=task.task_type,
            status=TaskStatus.RUNNING,
            result_data={},
            error_message=None,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            created_at=task.created_at,
        )
        return self.tasks.update(updated)

    def mark_task_succeeded(self, task_id: str, result_data: dict[str, Any]) -> Task:
        task = self.get_task(task_id)
        started_at = task.started_at or datetime.now(timezone.utc)
        updated = Task(
            id=task.id,
            session_id=task.session_id,
            task_type=task.task_type,
            status=TaskStatus.SUCCEEDED,
            result_data=result_data,
            error_message=None,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            created_at=task.created_at,
        )
        return self.tasks.update(updated)

    def mark_task_failed(self, task_id: str, error_message: str, result_data: dict[str, Any] | None = None) -> Task:
        task = self.get_task(task_id)
        started_at = task.started_at or datetime.now(timezone.utc)
        updated = Task(
            id=task.id,
            session_id=task.session_id,
            task_type=task.task_type,
            status=TaskStatus.FAILED,
            result_data=result_data or {},
            error_message=error_message,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            created_at=task.created_at,
        )
        return self.tasks.update(updated)

    def get_session_task_ids(self, session_id: str) -> list[str]:
        return [task.id for task in self.tasks.list_by_session(session_id)]

    def get_session_upload_ids(self, session_id: str) -> list[str]:
        return [upload.id for upload in self.uploads.list_by_session(session_id)]

    async def save_upload(self, session_id: str, upload_file: UploadFile) -> UploadedFile:
        self.get_session(session_id)
        file_bytes = await upload_file.read()
        file_id = f"upl_{uuid4().hex}"
        original_filename = upload_file.filename or "upload.bin"
        content_type = upload_file.content_type or "application/octet-stream"
        storage_key = upload_storage_key(
            session_id=session_id,
            upload_id=file_id,
            original_filename=original_filename,
        )
        storage_uri = self.storage.save_bytes(
            storage_key=storage_key,
            content=file_bytes,
        )

        uploaded = UploadedFile(
            id=file_id,
            session_id=session_id,
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=len(file_bytes),
            storage_backend=self.storage.backend_name,
            storage_key=storage_key,
            storage_uri=storage_uri,
        )
        created_upload = self.uploads.create(uploaded)

        if self.stored_files is not None:
            self.stored_files.create(
                StoredFile(
                    id=file_id,
                    session_id=session_id,
                    task_id=None,
                    kind="uploaded_source",
                    file_type=_infer_file_type(
                        original_filename=original_filename,
                        content_type=content_type,
                    ),
                    mime_type=content_type,
                    title=original_filename,
                    original_filename=original_filename,
                    storage_backend=self.storage.backend_name,
                    storage_key=storage_key,
                    storage_uri=storage_uri,
                    checksum_sha256=None,
                    size_bytes=len(file_bytes),
                )
            )

        return created_upload
