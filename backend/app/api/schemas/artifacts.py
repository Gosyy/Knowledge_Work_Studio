from datetime import datetime

from pydantic import BaseModel


class ArtifactSchema(BaseModel):
    id: str
    session_id: str
    task_id: str
    filename: str
    content_type: str
    storage_path: str
    size_bytes: int
    created_at: datetime
