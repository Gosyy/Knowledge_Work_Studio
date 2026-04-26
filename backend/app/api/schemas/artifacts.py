from datetime import datetime
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict

from backend.app.domain import Artifact


class ArtifactSchema(BaseModel):
    id: str
    session_id: str
    task_id: str
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
    download_url: str

    @classmethod
    def from_domain(cls, artifact: Artifact) -> "ArtifactSchema":
        safe_artifact_id = quote(artifact.id, safe="")
        return cls(
            id=artifact.id,
            session_id=artifact.session_id,
            task_id=artifact.task_id,
            filename=artifact.filename,
            content_type=artifact.content_type,
            size_bytes=artifact.size_bytes,
            created_at=artifact.created_at,
            download_url=f"/artifacts/{safe_artifact_id}/download",
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "art_903d8a",
                "session_id": "ses_4f2b1c",
                "task_id": "task_71f0d3",
                "filename": "summary.txt",
                "content_type": "text/plain",
                "size_bytes": 512,
                "created_at": "2026-04-22T12:01:03Z",
                "download_url": "/artifacts/art_903d8a/download",
            }
        }
    )
