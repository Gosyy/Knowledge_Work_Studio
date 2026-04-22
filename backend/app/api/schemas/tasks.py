from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.app.domain import TaskJobStatus, TaskStatus, TaskType


class TaskCreateRequest(BaseModel):
    session_id: str
    task_type: TaskType

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "ses_4f2b1c",
                "task_type": "pdf_summary",
            }
        }
    )


class TaskExecuteRequest(BaseModel):
    content: str | None = None
    uploaded_file_ids: list[str] = Field(default_factory=list)
    stored_file_ids: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
    presentation_ids: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Summarize the uploaded notes for the operator.",
                "uploaded_file_ids": ["upl_14be29"],
                "stored_file_ids": [],
                "document_ids": [],
                "presentation_ids": [],
            }
        }
    )


class TaskSemanticExecuteRequest(TaskExecuteRequest):
    workflow: str = Field(
        default="summarization",
        description="Semantic workflow: classification, summarization, rewriting, or outline_generation.",
    )
    instruction: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Rewrite this operator note for clarity.",
                "uploaded_file_ids": [],
                "stored_file_ids": [],
                "document_ids": [],
                "presentation_ids": [],
                "workflow": "rewriting",
                "instruction": "Make the text concise and professional.",
            }
        }
    )


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "task_71f0d3",
                "session_id": "ses_4f2b1c",
                "task_type": "pdf_summary",
                "status": "succeeded",
                "result_data": {
                    "artifact_ids": ["art_903d8a"],
                    "source_mode": "inline",
                    "source_refs": [],
                },
                "error_message": None,
                "started_at": "2026-04-22T12:01:00Z",
                "completed_at": "2026-04-22T12:01:03Z",
                "created_at": "2026-04-22T12:00:58Z",
            }
        }
    )


class TaskExecutionJobSchema(BaseModel):
    id: str
    task_id: str
    owner_user_id: str
    status: TaskJobStatus
    payload: dict[str, Any]
    error_message: str | None
    result_task_id: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "job_2dfab6",
                "task_id": "task_71f0d3",
                "owner_user_id": "user_local_default",
                "status": "queued",
                "payload": {
                    "content": "Summarize the uploaded notes for the operator.",
                    "uploaded_file_ids": ["upl_14be29"],
                    "stored_file_ids": [],
                    "document_ids": [],
                    "presentation_ids": [],
                },
                "error_message": None,
                "result_task_id": None,
                "created_at": "2026-04-22T12:00:59Z",
                "started_at": None,
                "completed_at": None,
            }
        }
    )
