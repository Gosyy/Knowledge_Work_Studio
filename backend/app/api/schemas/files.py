from datetime import datetime

from pydantic import BaseModel


class UploadedFileSchema(BaseModel):
    id: str
    session_id: str
    original_filename: str
    stored_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
