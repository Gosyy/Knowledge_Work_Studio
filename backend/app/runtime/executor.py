from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeExecutionRequest:
    code: str
    timeout_seconds: int = 30


class RuntimeExecutor:
    """Internal runtime boundary for controlled Python execution."""

    def execute(self, request: RuntimeExecutionRequest) -> str:
        raise NotImplementedError("RuntimeExecutor implementation is provided in a later issue")
