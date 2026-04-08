from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from backend.app.domain import Session, Task, TaskStatus, TaskType, UploadedFile
from backend.app.repositories import FileStorage, SessionRepository, TaskRepository, UploadedFileRepository


@dataclass
class SessionTaskService:
    sessions: SessionRepository
    tasks: TaskRepository
    uploads: UploadedFileRepository
    storage: FileStorage

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
        task = Task(id=f"task_{uuid4().hex}", session_id=session_id, task_type=task_type, status=TaskStatus.QUEUED)
        return self.tasks.create(task)

    def get_task(self, task_id: str) -> Task:
        task = self.tasks.get(task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return task

    def get_session_task_ids(self, session_id: str) -> list[str]:
        return [task.id for task in self.tasks.list_by_session(session_id)]

    def get_session_upload_ids(self, session_id: str) -> list[str]:
        return [upload.id for upload in self.uploads.list_by_session(session_id)]

    async def save_upload(self, session_id: str, upload_file: UploadFile) -> tuple[UploadedFile, Path]:
        self.get_session(session_id)
        file_bytes = await upload_file.read()
        file_id = f"upl_{uuid4().hex}"
        saved_path = self.storage.save_upload(
            session_id=session_id,
            upload_id=file_id,
            original_filename=upload_file.filename or "upload.bin",
            content=file_bytes,
        )

        uploaded = UploadedFile(
            id=file_id,
            session_id=session_id,
            original_filename=upload_file.filename or "upload.bin",
            content_type=upload_file.content_type or "application/octet-stream",
            size_bytes=len(file_bytes),
        )
        return self.uploads.create(uploaded), saved_path
