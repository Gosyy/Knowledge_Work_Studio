from __future__ import annotations

from threading import Lock

from backend.app.domain import Artifact, Session, Task, UploadedFile


class InMemorySessionRepository:
    def __init__(self) -> None:
        self._items: dict[str, Session] = {}
        self._lock = Lock()

    def create(self, session: Session) -> Session:
        with self._lock:
            self._items[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._items.get(session_id)


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._items: dict[str, Task] = {}
        self._lock = Lock()

    def create(self, task: Task) -> Task:
        with self._lock:
            self._items[task.id] = task
        return task

    def get(self, task_id: str) -> Task | None:
        return self._items.get(task_id)

    def list_by_session(self, session_id: str) -> list[Task]:
        return [task for task in self._items.values() if task.session_id == session_id]


class InMemoryArtifactRepository:
    def __init__(self) -> None:
        self._items: dict[str, Artifact] = {}
        self._lock = Lock()

    def create(self, artifact: Artifact) -> Artifact:
        with self._lock:
            self._items[artifact.id] = artifact
        return artifact

    def get(self, artifact_id: str) -> Artifact | None:
        return self._items.get(artifact_id)

    def list_by_session(self, session_id: str) -> list[Artifact]:
        return [artifact for artifact in self._items.values() if artifact.session_id == session_id]


class InMemoryUploadedFileRepository:
    def __init__(self) -> None:
        self._items: dict[str, UploadedFile] = {}
        self._lock = Lock()

    def create(self, uploaded_file: UploadedFile) -> UploadedFile:
        with self._lock:
            self._items[uploaded_file.id] = uploaded_file
        return uploaded_file

    def get(self, file_id: str) -> UploadedFile | None:
        return self._items.get(file_id)

    def list_by_session(self, session_id: str) -> list[UploadedFile]:
        return [file for file in self._items.values() if file.session_id == session_id]
