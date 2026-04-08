from __future__ import annotations

from typing import Protocol

from backend.app.domain import Artifact, Session, Task, UploadedFile


class SessionRepository(Protocol):
    def create(self, session: Session) -> Session: ...

    def get(self, session_id: str) -> Session | None: ...


class TaskRepository(Protocol):
    def create(self, task: Task) -> Task: ...

    def get(self, task_id: str) -> Task | None: ...

    def list_by_session(self, session_id: str) -> list[Task]: ...


class ArtifactRepository(Protocol):
    def create(self, artifact: Artifact) -> Artifact: ...


class UploadedFileRepository(Protocol):
    def create(self, uploaded_file: UploadedFile) -> UploadedFile: ...

    def get(self, file_id: str) -> UploadedFile | None: ...

    def list_by_session(self, session_id: str) -> list[UploadedFile]: ...
