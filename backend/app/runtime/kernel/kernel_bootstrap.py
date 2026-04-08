from __future__ import annotations

from dataclasses import dataclass

from backend.app.core.config import Settings
from backend.app.runtime.kernel.kernel_runtime import KernelRuntime
from backend.app.runtime.kernel.kernel_server import KernelServer, KernelServerConfig


@dataclass(frozen=True)
class KernelBootstrap:
    runtime: KernelRuntime
    server: KernelServer


def build_kernel_bootstrap(settings: Settings) -> KernelBootstrap:
    runtime = KernelRuntime()
    server = KernelServer(runtime=runtime, config=KernelServerConfig(auth_token=settings.kernel_server_auth_token))
    return KernelBootstrap(runtime=runtime, server=server)
