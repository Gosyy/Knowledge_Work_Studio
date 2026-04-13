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


def test_build_llm_provider_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported llm provider"):
        build_llm_provider(Settings(llm_provider="unknown"))


def provider_complete_request():
    from backend.app.integrations.llm import LLMCompletionRequest

    return LLMCompletionRequest(prompt="hello")
