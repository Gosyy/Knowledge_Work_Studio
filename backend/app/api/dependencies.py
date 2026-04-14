from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from backend.app.core.config import Settings, get_settings
from backend.app.integrations import get_storage_paths
from backend.app.integrations.file_storage import LocalFileStorage
from backend.app.integrations.llm import LLMProvider, build_llm_provider
from backend.app.orchestrator.execution import OrchestratorExecutionCoordinator
from backend.app.orchestrator.router import TaskRouter
from backend.app.repositories import (
    PostgresArtifactRepository,
    PostgresArtifactSourceRepository,
    PostgresDocumentRepository,
    PostgresExecutionRunRepository,
    PostgresPresentationRepository,
    PostgresSessionRepository,
    PostgresStoredFileRepository,
    PostgresTaskRepository,
    PostgresUploadedFileRepository,
    SqliteArtifactRepository,
    SqliteExecutionRunRepository,
    SqliteSessionRepository,
    SqliteTaskRepository,
    SqliteUploadedFileRepository,
)
from backend.app.repositories.sqlite import (
    SqliteArtifactSourceRepository,
    SqliteDocumentRepository,
    SqlitePresentationRepository,
    SqliteStoredFileRepository,
)
from backend.app.services import (
    ArtifactService,
    DataAnalysisService,
    DocxService,
    LLMTextService,
    PdfService,
    SessionTaskService,
    SlidesService,
    TaskExecutionService,
)
from backend.app.services.docx_service import DocxServiceEntrypoint
from backend.app.services.pdf_service import PdfServiceEntrypoint
from backend.app.services.slides_service import SlidesServiceEntrypoint
from backend.app.services.task_source_service import TaskSourceService

@dataclass
class AppContainer:
    artifact_service: ArtifactService
    session_task_service: SessionTaskService
    task_source_service: TaskSourceService


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


def _build_source_repositories(settings: Settings):
    backend = _resolve_metadata_backend(settings)
    if backend == "postgres":
        return (
            PostgresStoredFileRepository(settings.database_url),
            PostgresDocumentRepository(settings.database_url),
            PostgresPresentationRepository(settings.database_url),
            PostgresArtifactSourceRepository(settings.database_url),
        )
    return (
        SqliteStoredFileRepository(settings.repository_db_path),
        SqliteDocumentRepository(settings.repository_db_path),
        SqlitePresentationRepository(settings.repository_db_path),
        SqliteArtifactSourceRepository(settings.repository_db_path),
    )


def _build_execution_run_repository(settings: Settings):
    backend = _resolve_metadata_backend(settings)
    if backend == "postgres":
        return PostgresExecutionRunRepository(settings.database_url)
    return SqliteExecutionRunRepository(settings.repository_db_path)


def get_app_container(request: Request) -> AppContainer:
    if not hasattr(request.app.state, "app_container"):
        settings = get_app_settings()
        storage_paths = get_storage_paths(settings)
        storage = LocalFileStorage(storage_paths)

        sessions, tasks, uploads, artifacts = _build_repositories(settings)
        stored_files, documents, presentations, artifact_sources = _build_source_repositories(settings)

        request.app.state.app_container = AppContainer(
            session_task_service=SessionTaskService(
                sessions=sessions,
                tasks=tasks,
                uploads=uploads,
                storage=storage,
                stored_files=stored_files,
            ),
            artifact_service=ArtifactService(
                artifacts=artifacts,
                sessions=sessions,
                tasks=tasks,
                storage=storage,
            ),
            task_source_service=TaskSourceService(
                uploads=uploads,
                stored_files=stored_files,
                documents=documents,
                presentations=presentations,
                artifact_sources=artifact_sources,
                storage=storage,
            ),
        )
    return request.app.state.app_container


def get_session_task_service(request: Request) -> SessionTaskService:
    return get_app_container(request).session_task_service


def get_artifact_service(request: Request) -> ArtifactService:
    return get_app_container(request).artifact_service


def get_task_source_service(request: Request) -> TaskSourceService:
    return get_app_container(request).task_source_service


def get_official_execution_coordinator(request: Request) -> OrchestratorExecutionCoordinator:
    if not hasattr(request.app.state, "official_execution_coordinator"):
        container = get_app_container(request)
        settings = get_app_settings()
        request.app.state.official_execution_coordinator = OrchestratorExecutionCoordinator(
            task_router=TaskRouter(),
            session_task_service=container.session_task_service,
            task_execution_service=TaskExecutionService(
                session_task_service=container.session_task_service,
                execution_runs=_build_execution_run_repository(settings),
            ),
            artifact_service=container.artifact_service,
            data_service=DataAnalysisService.from_settings(settings),
            docx_service=DocxServiceEntrypoint(service=DocxService()),
            pdf_service=PdfServiceEntrypoint(service=PdfService()),
            slides_service=SlidesServiceEntrypoint(service=SlidesService()),
        )
    return request.app.state.official_execution_coordinator


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