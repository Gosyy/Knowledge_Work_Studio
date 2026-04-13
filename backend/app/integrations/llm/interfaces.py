from __future__ import annotations

from typing import Protocol

from backend.app.integrations.llm.models import LLMCompletionRequest, LLMCompletionResult


class LLMProvider(Protocol):
    provider_name: str

    def complete(self, request: LLMCompletionRequest) -> LLMCompletionResult: ...
