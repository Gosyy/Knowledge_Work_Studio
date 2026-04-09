from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from threading import Lock
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KernelExecutionRequest:
    code: str
    timeout_seconds: int = 30


@dataclass(frozen=True)
class KernelExecutionResult:
    session_id: str
    status: str
    submitted_at: datetime


@dataclass
class KernelSession:
    id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class KernelRuntime:
    """In-process kernel runtime boundary adapted for the modular monolith.

    This class intentionally does not start any external process at import time.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, KernelSession] = {}
        self._lock = Lock()

    def create_session(self) -> KernelSession:
        session = KernelSession(id=f"kernel_{uuid4().hex}")
        with self._lock:
            self._sessions[session.id] = session
        logger.info("Kernel session created", extra={"session_id": session.id})
        return session

    def get_session(self, session_id: str) -> KernelSession | None:
        return self._sessions.get(session_id)

    def shutdown_session(self, session_id: str) -> bool:
        with self._lock:
            removed = self._sessions.pop(session_id, None)
        if removed is not None:
            logger.info("Kernel session shutdown", extra={"session_id": session_id})
        return removed is not None

    def execute(self, session_id: str, request: KernelExecutionRequest) -> KernelExecutionResult:
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Unknown kernel session: {session_id}")

        now = datetime.now(timezone.utc)
        session.last_activity_at = now
        logger.info(
            "Kernel execution accepted",
            extra={"session_id": session_id, "timeout_seconds": request.timeout_seconds},
        )
        return KernelExecutionResult(session_id=session_id, status="accepted", submitted_at=now)

    def active_session_count(self) -> int:
        return len(self._sessions)
