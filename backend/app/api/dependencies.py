from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from backend.app.core.config import Settings, get_settings
from backend.app.integrations import get_storage_paths
from backend.app.integrations.file_storage import LocalFileStorage
from backend.app.integrations.llm import LLMProvider, build_llm_provider
from backend.app.repositories import (
    PostgresArtifactRepository,
    PostgresSessionRepository,
    PostgresTaskRepository,
    PostgresUploadedFileRepository,
    SqliteArtifactRepository,
    SqliteSessionRepository,
    SqliteTaskRepository,
    SqliteUploadedFileRepository,
)
from backend.app.services import ArtifactService, LLMTextService, SessionTaskService

@dataclass
class AppContainer:
    artifact_service: ArtifactService
    session_task_service: SessionTaskService


def get_app_settings() -> Settings:
    return get_settings()


def _resolve_metadata_backend(settings: Settings) -> str:
    backend = settings.metadata_backend.lower()
    if backend == "sqlite" and not settings.sqlite_runtime_allowed:
        raise ValueError(
            "SQLite metadata backend is disabled for runtime usage. "
            "Use METADATA_BACKEND=postgres (default production truth layer), "
            "or explicitly set SQLITE_RUNTIME_ALLOWED=true for tests."
        )
    if backend == "sqlite" and settings.app_env.lower() not in {"development", "test"}:
        raise ValueError(
            "SQLite metadata backend is only allowed in development/test environments. "
            "Use METADATA_BACKEND=postgres for production runtime."
        )
    if backend not in {"postgres", "sqlite"}:
        raise ValueError(f"Unsupported metadata backend: {settings.metadata_backend}")
    return backend


def _build_repositories(settings: Settings):
    backend = _resolve_metadata_backend(settings)
    if backend == "postgres":
        return (
            PostgresSessionRepository(settings.database_url),
            PostgresTaskRepository(settings.database_url),
            PostgresUploadedFileRepository(settings.database_url),
            PostgresArtifactRepository(settings.database_url),
        )
    return (
        SqliteSessionRepository(settings.repository_db_path),
        SqliteTaskRepository(settings.repository_db_path),
        SqliteUploadedFileRepository(settings.repository_db_path),
        SqliteArtifactRepository(settings.repository_db_path),
    )


def get_app_container(request: Request) -> AppContainer:
    if not hasattr(request.app.state, "app_container"):
        settings = get_app_settings()
        storage_paths = get_storage_paths(settings)
        storage = LocalFileStorage(storage_paths)

        sessions, tasks, uploads, artifacts = _build_repositories(settings)

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

def get_llm_provider(request: Request) -> LLMProvider:
    if not hasattr(request.app.state, "llm_provider"):
        request.app.state.llm_provider = build_llm_provider(get_app_settings())
    return request.app.state.llm_provider


def get_llm_text_service(request: Request) -> LLMTextService:
    if not hasattr(request.app.state, "llm_text_service"):
        request.app.state.llm_text_service = LLMTextService(
            provider=get_llm_provider(request)
        )
    return request.app.state.llm_text_service