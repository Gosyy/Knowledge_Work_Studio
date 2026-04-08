from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from backend.app.core.config import Settings, get_settings
from backend.app.integrations import get_storage_paths
from backend.app.integrations.file_storage import LocalFileStorage
from backend.app.repositories import InMemorySessionRepository, InMemoryTaskRepository, InMemoryUploadedFileRepository
from backend.app.services import SessionTaskService


@dataclass
class AppContainer:
    session_task_service: SessionTaskService


def get_app_settings() -> Settings:
    return get_settings()


def get_app_container(request: Request) -> AppContainer:
    if not hasattr(request.app.state, "app_container"):
        settings = get_app_settings()
        storage_paths = get_storage_paths(settings)
        storage = LocalFileStorage(storage_paths)
        request.app.state.app_container = AppContainer(
            session_task_service=SessionTaskService(
                sessions=InMemorySessionRepository(),
                tasks=InMemoryTaskRepository(),
                uploads=InMemoryUploadedFileRepository(),
                storage=storage,
            )
        )
    return request.app.state.app_container


def get_session_task_service(request: Request) -> SessionTaskService:
    return get_app_container(request).session_task_service
