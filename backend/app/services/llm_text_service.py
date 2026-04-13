from __future__ import annotations

from dataclasses import dataclass

from backend.app.integrations.llm import LLMCompletionRequest, LLMProvider


@dataclass
class LLMTextService:
    provider: LLMProvider

    def complete_prompt(self, prompt: str, *, system_prompt: str | None = None) -> str:
        result = self.provider.complete(
            LLMCompletionRequest(
                prompt=prompt,
                system_prompt=system_prompt,
            )
        )
        return result.text
