from datetime import datetime

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "upl_14be29",
                "session_id": "ses_4f2b1c",
                "original_filename": "notes.txt",
                "stored_filename": "notes.txt",
                "content_type": "text/plain",
                "size_bytes": 2048,
                "storage_backend": "local",
                "storage_key": "uploads/ses_4f2b1c/upl_14be29/notes.txt",
                "storage_uri": "local://uploads/ses_4f2b1c/upl_14be29/notes.txt",
                "created_at": "2026-04-22T12:00:30Z",
            }
        }
    )
