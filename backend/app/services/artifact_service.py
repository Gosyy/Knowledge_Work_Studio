from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fastapi import HTTPException, status

from backend.app.domain import Artifact
from backend.app.integrations.storage import artifact_storage_key
from backend.app.repositories import ArtifactRepository, FileStorage, SessionRepository, TaskRepository


@dataclass
class ArtifactService:
    artifacts: ArtifactRepository
    sessions: SessionRepository
    tasks: TaskRepository
    storage: FileStorage

    def get_artifact(self, artifact_id: str) -> Artifact:
        artifact = self.artifacts.get(artifact_id)
        if artifact is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
        return artifact

    def list_session_artifacts(self, session_id: str) -> list[Artifact]:
        session = self.sessions.get(session_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return self.artifacts.list_by_session(session_id)

    def get_artifact_download(self, artifact_id: str) -> tuple[Artifact, bytes]:
        artifact = self.get_artifact(artifact_id)
        if not self.storage.exists(storage_key=artifact.storage_key):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact file not found")
        return artifact, self.storage.read_bytes(storage_key=artifact.storage_key)

    def create_placeholder_artifact(
        self,
        *,
        session_id: str,
        task_id: str,
        filename: str,
        content_type: str,
    ) -> Artifact:
        if self.sessions.get(session_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if self.tasks.get(task_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        artifact_id = f"art_{uuid4().hex}"
        storage_key = artifact_storage_key(
            session_id=session_id,
            task_id=task_id,
            artifact_id=artifact_id,
            filename=filename,
        )
        storage_uri = self.storage.save_bytes(
            storage_key=storage_key,
            content=b"",
        )

        artifact = Artifact(
            id=artifact_id,
            session_id=session_id,
            task_id=task_id,
            filename=filename,
            content_type=content_type,
            storage_backend=self.storage.backend_name,
            storage_key=storage_key,
            storage_uri=storage_uri,
            size_bytes=0,
        )
        return self.artifacts.create(artifact)

    def create_artifact_from_bytes(
        self,
        *,
        session_id: str,
        task_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Artifact:
        if self.sessions.get(session_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if self.tasks.get(task_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        artifact_id = f"art_{uuid4().hex}"
        storage_key = artifact_storage_key(
            session_id=session_id,
            task_id=task_id,
            artifact_id=artifact_id,
            filename=filename,
        )
        storage_uri = self.storage.save_bytes(
            storage_key=storage_key,
            content=content,
        )
        artifact = Artifact(
            id=artifact_id,
            session_id=session_id,
            task_id=task_id,
            filename=filename,
            content_type=content_type,
            storage_backend=self.storage.backend_name,
            storage_key=storage_key,
            storage_uri=storage_uri,
            size_bytes=len(content),
        )
        return self.artifacts.create(artifact)
