from __future__ import annotations

from dataclasses import dataclass

from backend.app.core.config import Settings
from backend.app.runtime.kernel.kernel_bootstrap import KernelBootstrap, build_kernel_bootstrap


@dataclass
class KernelRuntimeInterface:
    """Orchestrator-safe internal interface for kernel control-plane access."""

    bootstrap: KernelBootstrap

    @classmethod
    def from_settings(cls, settings: Settings) -> "KernelRuntimeInterface":
        return cls(bootstrap=build_kernel_bootstrap(settings))

    def create_session(self) -> str:
        session = self.bootstrap.server.create_session(auth_token="")
        return session.id

    def execute(self, *, session_id: str, code: str, timeout_seconds: int = 30) -> str:
        result = self.bootstrap.server.execute(
            session_id=session_id,
            code=code,
            timeout_seconds=timeout_seconds,
            auth_token="",
        )
        return result.status

    def shutdown_session(self, session_id: str) -> bool:
        return self.bootstrap.server.shutdown_session(session_id=session_id, auth_token="")

    def active_sessions(self) -> int:
        return self.bootstrap.server.health(auth_token="")["active_sessions"]
