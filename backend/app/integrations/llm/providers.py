from __future__ import annotations

from dataclasses import dataclass

from backend.app.integrations.llm.models import LLMCompletionRequest, LLMCompletionResult


@dataclass(frozen=True)
class FakeLLMProvider:
    response_text: str = "NOOP_LLM_RESPONSE"
    model_name: str = "fake-llm-v1"
    provider_name: str = "fake"

    def complete(self, request: LLMCompletionRequest) -> LLMCompletionResult:
        _ = request
        return LLMCompletionResult(
            text=self.response_text,
            provider=self.provider_name,
            model=self.model_name,
            raw={"mode": "fake"},
        )


@dataclass(frozen=True)
class GigaChatProvider:
    api_base_url: str
    model_name: str
    client_id: str
    client_secret: str
    provider_name: str = "gigachat"

    def complete(self, request: LLMCompletionRequest) -> LLMCompletionResult:
        _ = request
        raise NotImplementedError(
            "GigaChat provider bootstrap is configured, but request execution is not implemented in F5."
        )
