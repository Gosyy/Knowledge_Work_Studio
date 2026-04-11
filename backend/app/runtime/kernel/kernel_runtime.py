from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import csv
import io
import json
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
    output_text: str | None = None


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
        output_text = self._execute_code(request.code)
        return KernelExecutionResult(session_id=session_id, status="accepted", submitted_at=now, output_text=output_text)

    @staticmethod
    def _execute_code(code: str) -> str | None:
        if not code.startswith("DATA_ANALYSIS::"):
            return None

        payload_raw = code.split("DATA_ANALYSIS::", 1)[1]
        payload = json.loads(payload_raw)
        content = payload.get("content", "")
        return KernelRuntime._summarize_tabular_content(content)

    @staticmethod
    def _summarize_tabular_content(content: str) -> str:
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            return "No rows detected in dataset."

        header = rows[0]
        data_rows = rows[1:] if len(rows) > 1 else []
        column_count = len(header)
        row_count = len(data_rows)

        numeric_values: list[float] = []
        for row in data_rows:
            for value in row:
                try:
                    numeric_values.append(float(value))
                except ValueError:
                    continue

        numeric_mean_text = "n/a"
        if numeric_values:
            numeric_mean_text = f"{sum(numeric_values) / len(numeric_values):.4f}"

        return (
            f"Rows: {row_count}\n"
            f"Columns: {column_count}\n"
            f"Numeric cells: {len(numeric_values)}\n"
            f"Numeric mean: {numeric_mean_text}"
        )

    def active_session_count(self) -> int:
        return len(self._sessions)
