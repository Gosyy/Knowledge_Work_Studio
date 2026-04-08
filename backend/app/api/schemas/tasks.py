from datetime import datetime

from pydantic import BaseModel

from backend.app.domain import TaskStatus, TaskType


class TaskCreateRequest(BaseModel):
    session_id: str
    task_type: TaskType


class TaskSchema(BaseModel):
    id: str
    session_id: str
    task_type: TaskType
    status: TaskStatus
    created_at: datetime
