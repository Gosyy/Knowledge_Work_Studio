from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    DOCX_EDIT = "docx_edit"
    PDF_SUMMARY = "pdf_summary"
    SLIDES_GENERATE = "slides_generate"
    DATA_ANALYSIS = "data_analysis"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class Task:
    id: str
    session_id: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    result_data: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
