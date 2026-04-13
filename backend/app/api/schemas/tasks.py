from datetime import datetime
from typing import Any

from pydantic import BaseModel

from backend.app.domain import TaskStatus, TaskType


class TaskCreateRequest(BaseModel):
    session_id: str
    task_type: TaskType


class TaskExecuteRequest(BaseModel):
    content: str


class TaskSchema(BaseModel):
    id: str
    session_id: str
    task_type: TaskType
    status: TaskStatus
    result_data: dict[str, Any]
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
