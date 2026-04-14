from __future__ import annotations

from backend.app.core.config import Settings
from backend.app.integrations.llm.interfaces import LLMProvider
from backend.app.integrations.llm.providers import FakeLLMProvider, GigaChatProvider


def build_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.strip().lower()

    if provider == "gigachat":
        return GigaChatProvider(
            api_base_url=settings.gigachat_api_base_url,
            auth_url=settings.gigachat_auth_url,
            scope=settings.gigachat_scope,
            model_name=settings.gigachat_model,
            client_id=settings.gigachat_client_id,
            client_secret=settings.gigachat_client_secret,
            timeout_seconds=settings.gigachat_timeout_seconds,
            verify_ssl=settings.gigachat_verify_ssl,
        )

    if provider in {"fake", "noop"}:
        return FakeLLMProvider(response_text=settings.fake_llm_response)

    raise ValueError(f"Unsupported llm provider: {settings.llm_provider}")
