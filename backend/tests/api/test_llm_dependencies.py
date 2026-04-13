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


def test_get_llm_text_service_uses_cached_provider(monkeypatch) -> None:
    monkeypatch.setattr(
        dependencies,
        "get_app_settings",
        lambda: Settings(llm_provider="fake", fake_llm_response="service-response"),
    )
    request = build_request()

    service = dependencies.get_llm_text_service(request)
    assert service is dependencies.get_llm_text_service(request)
    assert service.provider is dependencies.get_llm_provider(request)
    assert service.complete_prompt("hello") == "service-response"
