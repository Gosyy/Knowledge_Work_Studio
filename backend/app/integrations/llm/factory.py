from __future__ import annotations

from backend.app.core.config import Settings
from backend.app.integrations.llm.interfaces import LLMProvider
from backend.app.integrations.llm.gigachat_runtime import validate_llm_runtime_selection
from backend.app.integrations.llm.providers import FakeLLMProvider, GigaChatProvider, LiteLLMCompatibleProvider


def build_llm_provider(settings: Settings) -> LLMProvider:
    validate_llm_runtime_selection(settings)
    provider = settings.llm_provider.strip().lower()
    transport_mode = settings.llm_transport_mode.strip().lower()

    if provider == "gigachat" and transport_mode in {"", "direct_gigachat"}:
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

    if provider == "gigachat" and transport_mode == "litellm_gateway":
        return LiteLLMCompatibleProvider(
            api_base_url=settings.litellm_gateway_url,
            model_name=settings.litellm_gateway_model or settings.gigachat_model,
            api_key=settings.litellm_gateway_api_key,
            timeout_seconds=settings.litellm_gateway_timeout_seconds,
            verify_ssl=settings.litellm_gateway_verify_ssl,
        )

    if provider in {"fake", "noop"}:
        return FakeLLMProvider(response_text=settings.fake_llm_response)

    raise ValueError(f"Unsupported llm provider/transport: {settings.llm_provider}/{settings.llm_transport_mode}")
