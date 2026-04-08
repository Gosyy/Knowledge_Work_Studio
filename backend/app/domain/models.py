from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    DOCX_EDIT = "docx_edit"
    PDF_SUMMARY = "pdf_summary"
    SLIDES_GENERATION = "slides_generation"
    DATA_ANALYSIS = "data_analysis"


class Session(BaseModel):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Task(BaseModel):
    id: str
    session_id: str
    task_type: TaskType
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Artifact(BaseModel):
    id: str
    session_id: str
    task_id: str
    filename: str
    content_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
