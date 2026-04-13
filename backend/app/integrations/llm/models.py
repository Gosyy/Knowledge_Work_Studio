from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LLMCompletionRequest:
    prompt: str
    system_prompt: str | None = None
    temperature: float = 0.2


@dataclass(frozen=True)
class LLMCompletionResult:
    text: str
    provider: str
    model: str
    raw: dict[str, Any] | None = None
