from datetime import datetime

from pydantic import BaseModel


class UploadedFileSchema(BaseModel):
    id: str
    session_id: str
    original_filename: str
    stored_filename: str
    content_type: str
    size_bytes: int
    storage_backend: str
    storage_key: str
    storage_uri: str
    created_at: datetime
