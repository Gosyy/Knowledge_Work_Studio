from datetime import datetime

from pydantic import BaseModel


class ArtifactSchema(BaseModel):
    id: str
    session_id: str
    task_id: str
    filename: str
    content_type: str
    created_at: datetime
