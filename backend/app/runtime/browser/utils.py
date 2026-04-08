from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Protocol


class BrowserController(Protocol):
    name: str

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def is_healthy(self) -> bool: ...


@dataclass(frozen=True)
class BrowserRuntimeConfig:
    enabled: bool
    preferred_backend: str
    allow_unsafe_features: bool
    max_restart_attempts: int


_TRUTHY_VALUES = {"1", "true", "yes", "on"}


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUTHY_VALUES


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(value, 0)


def load_browser_runtime_config() -> BrowserRuntimeConfig:
    return BrowserRuntimeConfig(
        enabled=env_flag("KW_BROWSER_RUNTIME_ENABLED", default=False),
        preferred_backend=os.getenv("KW_BROWSER_BACKEND", "playwright").strip().lower(),
        allow_unsafe_features=env_flag("KW_BROWSER_ALLOW_UNSAFE", default=False),
        max_restart_attempts=env_int("KW_BROWSER_MAX_RESTARTS", default=2),
    )
