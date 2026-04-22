from datetime import datetime

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "art_903d8a",
                "session_id": "ses_4f2b1c",
                "task_id": "task_71f0d3",
                "filename": "summary.txt",
                "content_type": "text/plain",
                "storage_backend": "local",
                "storage_key": "artifacts/ses_4f2b1c/task_71f0d3/art_903d8a/summary.txt",
                "storage_uri": "local://artifacts/ses_4f2b1c/task_71f0d3/art_903d8a/summary.txt",
                "size_bytes": 512,
                "created_at": "2026-04-22T12:01:03Z",
            }
        }
    )
