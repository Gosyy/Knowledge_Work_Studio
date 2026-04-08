from __future__ import annotations

from dataclasses import asdict, dataclass

from backend.app.runtime.kernel.kernel_runtime import KernelRuntime


@dataclass(frozen=True)
class KernelRuntimeSnapshot:
    active_sessions: int


class KernelInspector:
    def __init__(self, runtime: KernelRuntime) -> None:
        self._runtime = runtime

    def snapshot(self) -> KernelRuntimeSnapshot:
        return KernelRuntimeSnapshot(active_sessions=self._runtime.active_session_count())

    def snapshot_dict(self) -> dict[str, int]:
        return asdict(self.snapshot())
