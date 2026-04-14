import pytest

from backend.app.core.config import Settings
from backend.app.integrations.llm import FakeLLMProvider, GigaChatProvider, build_llm_provider


def test_build_llm_provider_defaults_to_gigachat() -> None:
    provider = build_llm_provider(Settings())
    assert isinstance(provider, GigaChatProvider)
    assert provider.provider_name == "gigachat"


def test_build_llm_provider_supports_fake_test_mode() -> None:
    provider = build_llm_provider(Settings(llm_provider="fake", fake_llm_response="ok"))
    assert isinstance(provider, FakeLLMProvider)
    assert provider.complete(request=provider_complete_request()).text == "ok"


def test_build_llm_provider_supports_noop_alias() -> None:
    provider = build_llm_provider(Settings(llm_provider="noop", fake_llm_response="noop-ok"))
    assert isinstance(provider, FakeLLMProvider)
    assert provider.complete(request=provider_complete_request()).text == "noop-ok"


def test_build_llm_provider_wires_gigachat_runtime_settings() -> None:
    provider = build_llm_provider(
        Settings(
            llm_provider=" gigachat ",
            gigachat_api_base_url="https://gigachat.internal.local/api/v1",
            gigachat_auth_url="https://auth.internal.local/oauth",
            gigachat_scope="GIGACHAT_API_B2B",
            gigachat_model="GigaChat-Max",
            gigachat_client_id="client-id",
            gigachat_client_secret="client-secret",
            gigachat_timeout_seconds=12.5,
            gigachat_verify_ssl=False,
        )
    )
    assert isinstance(provider, GigaChatProvider)
    assert (
        provider.api_base_url,
        provider.auth_url,
        provider.scope,
        provider.model_name,
        provider.client_id,
        provider.client_secret,
        provider.timeout_seconds,
        provider.verify_ssl,
    ) == (
        "https://gigachat.internal.local/api/v1",
        "https://auth.internal.local/oauth",
        "GIGACHAT_API_B2B",
        "GigaChat-Max",
        "client-id",
        "client-secret",
        12.5,
        False,
    )


def test_build_llm_provider_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported llm provider"):
        build_llm_provider(Settings(llm_provider="unknown"))


def test_gigachat_provider_requires_credentials_before_runtime_call() -> None:
    provider = build_llm_provider(Settings(llm_provider="gigachat"))

    with pytest.raises(ValueError, match="gigachat_client_id"):
        provider.complete(request=provider_complete_request())


def provider_complete_request():
    from backend.app.integrations.llm import LLMCompletionRequest

    return LLMCompletionRequest(prompt="hello")
