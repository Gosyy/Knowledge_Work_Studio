from __future__ import annotations

from dataclasses import dataclass

from backend.app.runtime.browser.browser_supervisor import BrowserSupervisor


@dataclass
class BrowserRuntimeInterface:
    """Internal-only orchestrator-safe interface for browser runtime control."""

    supervisor: BrowserSupervisor

    @classmethod
    def from_env(cls) -> "BrowserRuntimeInterface":
        return cls(supervisor=BrowserSupervisor.from_env())

    async def start(self) -> None:
        await self.supervisor.start()

    async def stop(self) -> None:
        await self.supervisor.stop()

    async def ensure_healthy(self) -> bool:
        return await self.supervisor.ensure_healthy()

    @property
    def enabled(self) -> bool:
        return self.supervisor.config.enabled
