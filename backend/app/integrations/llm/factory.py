from __future__ import annotations

from backend.app.core.config import Settings
from backend.app.integrations.llm.interfaces import LLMProvider
from backend.app.integrations.llm.providers import FakeLLMProvider, GigaChatProvider


def build_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.strip().lower()

    if provider == "gigachat":
        return GigaChatProvider(
            api_base_url=settings.gigachat_api_base_url,
            model_name=settings.gigachat_model,
            client_id=settings.gigachat_client_id,
            client_secret=settings.gigachat_client_secret,
        )

    if provider in {"fake", "noop"}:
        return FakeLLMProvider(response_text=settings.fake_llm_response)

    raise ValueError(f"Unsupported llm provider: {settings.llm_provider}")
