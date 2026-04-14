from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.app.domain import TaskStatus, TaskType


class TaskCreateRequest(BaseModel):
    session_id: str
    task_type: TaskType


class TaskExecuteRequest(BaseModel):
    content: str | None = None
    uploaded_file_ids: list[str] = Field(default_factory=list)
    stored_file_ids: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
    presentation_ids: list[str] = Field(default_factory=list)


class TaskSemanticExecuteRequest(TaskExecuteRequest):
    workflow: str = Field(
        default="summarization",
        description="Semantic workflow: classification, summarization, rewriting, or outline_generation.",
    )
    instruction: str | None = None


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
