from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TaskJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class TaskExecutionJob:
    id: str
    task_id: str
    owner_user_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    status: TaskJobStatus = TaskJobStatus.QUEUED
    error_message: str | None = None
    result_task_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
