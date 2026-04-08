from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fastapi import HTTPException, status

from backend.app.domain import Artifact
from backend.app.repositories import ArtifactRepository, SessionRepository, TaskRepository


@dataclass
class ArtifactService:
    artifacts: ArtifactRepository
    sessions: SessionRepository
    tasks: TaskRepository

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

        artifact = Artifact(
            id=f"art_{uuid4().hex}",
            session_id=session_id,
            task_id=task_id,
            filename=filename,
            content_type=content_type,
        )
        return self.artifacts.create(artifact)
