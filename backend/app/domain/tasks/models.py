from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class TaskType(str, Enum):
    DOCX_EDIT = "docx_edit"
    PDF_SUMMARY = "pdf_summary"
    SLIDES_GENERATE = "slides_generate"
    DATA_ANALYSIS = "data_analysis"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class Task:
    id: str
    session_id: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.QUEUED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
