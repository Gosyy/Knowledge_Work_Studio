from fastapi import FastAPI
from starlette.requests import Request

from backend.app.api import dependencies
from backend.app.core.config import Settings
from backend.app.integrations.llm import FakeLLMProvider, LLMCompletionRequest


def build_request() -> Request:
    app = FastAPI()
    scope = {
        "type": "http",
        "app": app,
        "method": "GET",
        "path": "/",
        "headers": [],
    }
    return Request(scope)


def test_get_llm_provider_caches_instance_on_app_state(monkeypatch) -> None:
    monkeypatch.setattr(
        dependencies,
        "get_app_settings",
        lambda: Settings(llm_provider="fake", fake_llm_response="cached-response"),
    )
    request = build_request()

    provider_1 = dependencies.get_llm_provider(request)
    provider_2 = dependencies.get_llm_provider(request)

    assert provider_1 is provider_2
    assert isinstance(provider_1, FakeLLMProvider)
    result = provider_1.complete(request=LLMCompletionRequest(prompt="hi"))
    assert result.text == "cached-response"


def test_get_llm_text_service_uses_cached_provider(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        dependencies,
        "get_app_settings",
        lambda: Settings(
            llm_provider="fake",
            fake_llm_response="service-response",
            metadata_backend="sqlite",
            sqlite_runtime_allowed=True,
            repository_db_path=str(tmp_path / "repositories.sqlite3"),
        ),
    )
    request = build_request()

    service = dependencies.get_llm_text_service(request)
    assert service is dependencies.get_llm_text_service(request)
    assert service.provider is dependencies.get_llm_provider(request)
    assert service.complete_prompt("hello") == "service-response"


def test_get_llm_text_service_wires_llm_run_repository(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("REPOSITORY_DB_PATH", str(tmp_path / "repositories.sqlite3"))
    from backend.app.core.config import get_settings

    get_settings.cache_clear()
    request = build_request()

    service = dependencies.get_llm_text_service(request)

    assert service.llm_runs is not None


def test_l1_dependencies_module_delegates_container_building(monkeypatch, tmp_path) -> None:
    settings = Settings(
        metadata_backend="sqlite",
        sqlite_runtime_allowed=True,
        repository_db_path=str(tmp_path / "repositories.sqlite3"),
        storage_root=str(tmp_path / "storage"),
        uploads_dir=str(tmp_path / "storage" / "uploads"),
        artifacts_dir=str(tmp_path / "storage" / "artifacts"),
        temp_dir=str(tmp_path / "storage" / "temp"),
    )
    calls = []

    def fake_build_app_container(received_settings):
        calls.append(received_settings)
        return dependencies.AppContainer(
            artifact_service=object(),
            session_task_service=object(),
            task_source_service=object(),
        )

    monkeypatch.setattr(dependencies, "get_app_settings", lambda: settings)
    monkeypatch.setattr(dependencies, "build_app_container", fake_build_app_container)
    request = build_request()

    assert dependencies.get_app_container(request) is dependencies.get_app_container(request)
    assert calls == [settings]
