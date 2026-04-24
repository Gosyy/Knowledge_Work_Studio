from __future__ import annotations

from dataclasses import dataclass

from backend.app.core.config import Settings
from backend.app.integrations import get_storage_paths
from backend.app.integrations.file_storage import LocalFileStorage, RemoteObjectStorage, S3CompatibleFileStorage
from backend.app.integrations.queue import InMemoryTaskExecutionQueue, TaskExecutionQueue
from backend.app.repositories.storage import FileStorage
from backend.app.integrations.llm import LLMProvider
from backend.app.integrations.llm import build_llm_provider as build_provider_from_settings
from backend.app.orchestrator.execution import OrchestratorExecutionCoordinator
from backend.app.orchestrator.router import TaskRouter
from backend.app.repositories import (
    PostgresArtifactRepository,
    PostgresArtifactSourceRepository,
    PostgresDerivedContentRepository,
    PostgresDocumentRepository,
    PostgresExecutionRunRepository,
    PostgresLLMRunRepository,
    PostgresPresentationRepository,
    PostgresPresentationVersionRepository,
    PostgresSessionRepository,
    PostgresStoredFileRepository,
    PostgresTaskRepository,
    PostgresUploadedFileRepository,
    SqliteArtifactRepository,
    SqliteExecutionRunRepository,
    SqliteLLMRunRepository,
    SqliteSessionRepository,
    SqliteTaskRepository,
    SqliteUploadedFileRepository,
)
from backend.app.repositories.sqlite import (
    SqliteArtifactSourceRepository,
    SqliteDerivedContentRepository,
    SqliteDocumentRepository,
    SqlitePresentationRepository,
    SqlitePresentationVersionRepository,
    SqliteStoredFileRepository,
)
from backend.app.services import (
    ArtifactService,
    DataAnalysisService,
    DocxService,
    LLMTextService,
    PdfService,
    PresentationCatalogService,
    SessionTaskService,
    SlidesService,
    TaskExecutionService,
    TaskQueueService,
)
from backend.app.services.docx_service import DocxServiceEntrypoint
from backend.app.services.pdf_service import PdfServiceEntrypoint
from backend.app.services.slides_service import SlidesServiceEntrypoint, SlideImageRegistry
from backend.app.services.task_source_service import TaskSourceService


@dataclass(frozen=True)
class RepositoryBundle:
    sessions: object
    tasks: object
    uploads: object
    artifacts: object


@dataclass(frozen=True)
class SourceRepositoryBundle:
    stored_files: object
    documents: object
    presentations: object
    presentation_versions: object
    artifact_sources: object
    derived_contents: object


@dataclass(frozen=True)
class AppContainer:
    artifact_service: ArtifactService
    session_task_service: SessionTaskService
    task_source_service: TaskSourceService
    presentation_catalog_service: PresentationCatalogService | None = None


def resolve_metadata_backend(settings: Settings) -> str:
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


def build_repositories(settings: Settings) -> RepositoryBundle:
    backend = resolve_metadata_backend(settings)
    if backend == "postgres":
        return RepositoryBundle(
            sessions=PostgresSessionRepository(settings.database_url),
            tasks=PostgresTaskRepository(settings.database_url),
            uploads=PostgresUploadedFileRepository(settings.database_url),
            artifacts=PostgresArtifactRepository(settings.database_url),
        )
    return RepositoryBundle(
        sessions=SqliteSessionRepository(settings.repository_db_path),
        tasks=SqliteTaskRepository(settings.repository_db_path),
        uploads=SqliteUploadedFileRepository(settings.repository_db_path),
        artifacts=SqliteArtifactRepository(settings.repository_db_path),
    )


def build_source_repositories(settings: Settings) -> SourceRepositoryBundle:
    backend = resolve_metadata_backend(settings)
    if backend == "postgres":
        return SourceRepositoryBundle(
            stored_files=PostgresStoredFileRepository(settings.database_url),
            documents=PostgresDocumentRepository(settings.database_url),
            presentations=PostgresPresentationRepository(settings.database_url),
            presentation_versions=PostgresPresentationVersionRepository(settings.database_url),
            artifact_sources=PostgresArtifactSourceRepository(settings.database_url),
            derived_contents=PostgresDerivedContentRepository(settings.database_url),
        )
    return SourceRepositoryBundle(
        stored_files=SqliteStoredFileRepository(settings.repository_db_path),
        documents=SqliteDocumentRepository(settings.repository_db_path),
        presentations=SqlitePresentationRepository(settings.repository_db_path),
        presentation_versions=SqlitePresentationVersionRepository(settings.repository_db_path),
        artifact_sources=SqliteArtifactSourceRepository(settings.repository_db_path),
        derived_contents=SqliteDerivedContentRepository(settings.repository_db_path),
    )


def build_execution_run_repository(settings: Settings):
    backend = resolve_metadata_backend(settings)
    if backend == "postgres":
        return PostgresExecutionRunRepository(settings.database_url)
    return SqliteExecutionRunRepository(settings.repository_db_path)


def build_llm_run_repository(settings: Settings):
    backend = resolve_metadata_backend(settings)
    if backend == "postgres":
        return PostgresLLMRunRepository(settings.database_url)
    return SqliteLLMRunRepository(settings.repository_db_path)


def resolve_storage_backend(settings: Settings) -> str:
    backend = settings.storage_backend.strip().lower()
    if backend not in {"local", "remote_object_storage", "minio", "s3"}:
        raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
    return backend


def build_storage(settings: Settings) -> FileStorage:
    backend = resolve_storage_backend(settings)
    if backend == "local":
        return LocalFileStorage(get_storage_paths(settings))
    if backend == "remote_object_storage":
        return RemoteObjectStorage.from_settings(settings)
    if backend in {"minio", "s3"}:
        return S3CompatibleFileStorage.from_settings(settings)
    raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")


def build_app_container(settings: Settings) -> AppContainer:
    storage = build_storage(settings)
    repositories = build_repositories(settings)
    source_repositories = build_source_repositories(settings)

    session_task_service = SessionTaskService(
        sessions=repositories.sessions,
        tasks=repositories.tasks,
        uploads=repositories.uploads,
        storage=storage,
        stored_files=source_repositories.stored_files,
    )
    artifact_service = ArtifactService(
        artifacts=repositories.artifacts,
        sessions=repositories.sessions,
        tasks=repositories.tasks,
        storage=storage,
    )
    task_source_service = TaskSourceService(
        uploads=repositories.uploads,
        stored_files=source_repositories.stored_files,
        documents=source_repositories.documents,
        presentations=source_repositories.presentations,
        artifact_sources=source_repositories.artifact_sources,
        derived_contents=source_repositories.derived_contents,
        storage=storage,
    )
    presentation_catalog_service = PresentationCatalogService(
        session_task_service=session_task_service,
        presentations=source_repositories.presentations,
        stored_files=source_repositories.stored_files,
        presentation_versions=source_repositories.presentation_versions,
    )
    return AppContainer(
        artifact_service=artifact_service,
        session_task_service=session_task_service,
        task_source_service=task_source_service,
        presentation_catalog_service=presentation_catalog_service,
    )


def build_official_execution_coordinator(
    *,
    settings: Settings,
    container: AppContainer,
) -> OrchestratorExecutionCoordinator:
    storage = build_storage(settings)
    source_repositories = build_source_repositories(settings)
    return OrchestratorExecutionCoordinator(
        task_router=TaskRouter(),
        session_task_service=container.session_task_service,
        task_execution_service=TaskExecutionService(
            session_task_service=container.session_task_service,
            execution_runs=build_execution_run_repository(settings),
        ),
        artifact_service=container.artifact_service,
        data_service=DataAnalysisService.from_settings(settings),
        docx_service=DocxServiceEntrypoint(service=DocxService()),
        pdf_service=PdfServiceEntrypoint(service=PdfService()),
        slides_service=SlidesServiceEntrypoint(
            service=SlidesService(
                image_registry=SlideImageRegistry(storage=storage, stored_files=source_repositories.stored_files),
            )
        ),
    )


def build_task_queue_service(
    *,
    container: AppContainer,
    coordinator: OrchestratorExecutionCoordinator,
    queue: TaskExecutionQueue | None = None,
) -> TaskQueueService:
    return TaskQueueService(
        queue=queue or InMemoryTaskExecutionQueue(),
        session_task_service=container.session_task_service,
        task_source_service=container.task_source_service,
        coordinator=coordinator,
    )


def build_llm_provider(settings: Settings) -> LLMProvider:
    return build_provider_from_settings(settings)


def build_llm_text_service(*, settings: Settings, provider: LLMProvider) -> LLMTextService:
    return LLMTextService(
        provider=provider,
        llm_runs=build_llm_run_repository(settings),
    )
