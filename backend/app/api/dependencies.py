from __future__ import annotations

from fastapi import Request

from backend.app.composition import (
    AppContainer,
    build_app_container,
    build_llm_provider,
    build_llm_text_service,
    build_official_execution_coordinator,
)
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.llm import LLMProvider
from backend.app.orchestrator.execution import OrchestratorExecutionCoordinator
from backend.app.services import ArtifactService, LLMTextService, SessionTaskService
from backend.app.services.task_source_service import TaskSourceService


def get_app_settings() -> Settings:
    return get_settings()


def get_app_container(request: Request) -> AppContainer:
    if not hasattr(request.app.state, "app_container"):
        request.app.state.app_container = build_app_container(get_app_settings())
    return request.app.state.app_container


def get_session_task_service(request: Request) -> SessionTaskService:
    return get_app_container(request).session_task_service


def get_artifact_service(request: Request) -> ArtifactService:
    return get_app_container(request).artifact_service


def get_task_source_service(request: Request) -> TaskSourceService:
    return get_app_container(request).task_source_service


def get_official_execution_coordinator(request: Request) -> OrchestratorExecutionCoordinator:
    if not hasattr(request.app.state, "official_execution_coordinator"):
        request.app.state.official_execution_coordinator = build_official_execution_coordinator(
            settings=get_app_settings(),
            container=get_app_container(request),
        )
    return request.app.state.official_execution_coordinator


def get_llm_provider(request: Request) -> LLMProvider:
    if not hasattr(request.app.state, "llm_provider"):
        request.app.state.llm_provider = build_llm_provider(get_app_settings())
    return request.app.state.llm_provider


def get_llm_text_service(request: Request) -> LLMTextService:
    if not hasattr(request.app.state, "llm_text_service"):
        request.app.state.llm_text_service = build_llm_text_service(
            settings=get_app_settings(),
            provider=get_llm_provider(request),
        )
    return request.app.state.llm_text_service
