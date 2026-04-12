from datetime import datetime

from pydantic import BaseModel


class ArtifactSchema(BaseModel):
    id: str
    session_id: str
    task_id: str
    filename: str
    content_type: str
    storage_backend: str
    storage_key: str
    storage_uri: str
    size_bytes: int
    created_at: datetime
