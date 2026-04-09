from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import Request

from backend.app.core.config import Settings, get_settings
from backend.app.integrations import get_storage_paths
from backend.app.integrations.database import bootstrap_database
from backend.app.integrations.file_storage import LocalFileStorage
from backend.app.repositories import (
    SQLiteArtifactRepository,
    SQLiteSessionRepository,
    SQLiteTaskRepository,
    SQLiteUploadedFileRepository,
)
from backend.app.services import ArtifactService, SessionTaskService


@dataclass
class AppContainer:
    artifact_service: ArtifactService
    session_task_service: SessionTaskService


def get_app_settings() -> Settings:
    return get_settings()


def get_app_container(request: Request) -> AppContainer:
    if not hasattr(request.app.state, "app_container"):
        settings = get_app_settings()
        storage_paths = get_storage_paths(settings)
        storage = LocalFileStorage(storage_paths)
        database = bootstrap_database(
            db_path=Path(settings.sqlite_db_path),
            migrations_dir=Path(settings.sqlite_migrations_dir),
        )

        sessions = SQLiteSessionRepository(database)
        tasks = SQLiteTaskRepository(database)
        uploads = SQLiteUploadedFileRepository(database)
        artifacts = SQLiteArtifactRepository(database)

        request.app.state.app_container = AppContainer(
            session_task_service=SessionTaskService(
                sessions=sessions,
                tasks=tasks,
                uploads=uploads,
                storage=storage,
            ),
            artifact_service=ArtifactService(
                artifacts=artifacts,
                sessions=sessions,
                tasks=tasks,
                storage=storage,
            ),
        )
    return request.app.state.app_container


def get_session_task_service(request: Request) -> SessionTaskService:
    return get_app_container(request).session_task_service


def get_artifact_service(request: Request) -> ArtifactService:
    return get_app_container(request).artifact_service
