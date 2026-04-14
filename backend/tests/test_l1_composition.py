from pathlib import Path

import pytest

from backend.app.composition import (
    AppContainer,
    build_app_container,
    build_llm_provider,
    build_llm_text_service,
    build_official_execution_coordinator,
    resolve_metadata_backend,
)
from backend.app.core.config import Settings
from backend.app.integrations.llm import FakeLLMProvider
from backend.app.orchestrator.execution import OrchestratorExecutionCoordinator
from backend.app.services import LLMTextService


def sqlite_settings(tmp_path: Path) -> Settings:
    return Settings(
        metadata_backend="sqlite",
        sqlite_runtime_allowed=True,
        repository_db_path=str(tmp_path / "repositories.sqlite3"),
        storage_root=str(tmp_path / "storage"),
        uploads_dir=str(tmp_path / "storage" / "uploads"),
        artifacts_dir=str(tmp_path / "storage" / "artifacts"),
        temp_dir=str(tmp_path / "storage" / "temp"),
        llm_provider="fake",
        fake_llm_response="composition-response",
    )


def test_l1_composition_root_builds_explicit_app_container(tmp_path: Path) -> None:
    container = build_app_container(sqlite_settings(tmp_path))

    assert isinstance(container, AppContainer)
    assert container.session_task_service is not None
    assert container.artifact_service is not None
    assert container.task_source_service is not None
    assert container.task_source_service.storage is container.session_task_service.storage


def test_l1_composition_root_builds_execution_coordinator(tmp_path: Path) -> None:
    settings = sqlite_settings(tmp_path)
    container = build_app_container(settings)

    coordinator = build_official_execution_coordinator(settings=settings, container=container)

    assert isinstance(coordinator, OrchestratorExecutionCoordinator)


def test_l1_composition_root_builds_llm_provider_and_text_service(tmp_path: Path) -> None:
    settings = sqlite_settings(tmp_path)

    provider = build_llm_provider(settings)
    service = build_llm_text_service(settings=settings, provider=provider)

    assert isinstance(provider, FakeLLMProvider)
    assert isinstance(service, LLMTextService)
    assert service.complete_prompt("hello") == "composition-response"
    assert service.llm_runs is not None


def test_l1_composition_root_rejects_unsafe_sqlite_runtime() -> None:
    with pytest.raises(ValueError, match="SQLite metadata backend is disabled"):
        resolve_metadata_backend(Settings(metadata_backend="sqlite", sqlite_runtime_allowed=False))
