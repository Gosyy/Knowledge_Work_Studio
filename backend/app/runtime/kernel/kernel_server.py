from __future__ import annotations

from dataclasses import dataclass

from backend.app.runtime.kernel.kernel_runtime import KernelExecutionRequest, KernelExecutionResult, KernelRuntime, KernelSession


@dataclass(frozen=True)
class KernelServerConfig:
    auth_token: str = ""


class KernelServer:
    """Control-plane adapter for runtime/kernel operations.

    This is internal-only and not exposed as a public API router.
    """

    def __init__(self, runtime: KernelRuntime, config: KernelServerConfig) -> None:
        self._runtime = runtime
        self._config = config

    def _authorize(self, auth_token: str) -> None:
        if self._config.auth_token and auth_token != self._config.auth_token:
            raise PermissionError("Unauthorized kernel control-plane request")

    def create_session(self, *, auth_token: str = "") -> KernelSession:
        self._authorize(auth_token)
        return self._runtime.create_session()

    def execute(
        self,
        *,
        session_id: str,
        code: str,
        timeout_seconds: int = 30,
        auth_token: str = "",
    ) -> KernelExecutionResult:
        self._authorize(auth_token)
        return self._runtime.execute(
            session_id,
            KernelExecutionRequest(code=code, timeout_seconds=timeout_seconds),
        )

    def shutdown_session(self, *, session_id: str, auth_token: str = "") -> bool:
        self._authorize(auth_token)
        return self._runtime.shutdown_session(session_id)

    def health(self, *, auth_token: str = "") -> dict[str, int]:
        self._authorize(auth_token)
        return {"active_sessions": self._runtime.active_session_count()}
