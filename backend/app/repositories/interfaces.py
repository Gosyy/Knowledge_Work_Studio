from __future__ import annotations

from typing import Protocol

from backend.app.domain import Artifact, Session, Task


class SessionRepository(Protocol):
    def create(self, session: Session) -> Session: ...


class TaskRepository(Protocol):
    def create(self, task: Task) -> Task: ...


class ArtifactRepository(Protocol):
    def create(self, artifact: Artifact) -> Artifact: ...
