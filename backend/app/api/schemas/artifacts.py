from datetime import datetime

from pydantic import BaseModel


class ArtifactSchema(BaseModel):
    id: str
    session_id: str
    task_id: str
    filename: str
    content_type: str
    storage_path: str | None = None
    size_bytes: int | None = None
    created_at: datetime
