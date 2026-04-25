from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PresentationCurrentFileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: str
    file_type: str
    mime_type: str
    title: str | None
    original_filename: str | None
    checksum_sha256: str | None
    size_bytes: int | None
    created_at: datetime
    updated_at: datetime


class PresentationVersionSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version_number: int
    file_id: str
    parent_version_id: str | None
    change_summary: str | None
    created_at: datetime


class PresentationSchema(BaseModel):
    id: str
    session_id: str
    current_file_id: str | None
    presentation_type: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    current_file: PresentationCurrentFileSchema | None
    latest_version: PresentationVersionSummarySchema | None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "pres_123",
                "session_id": "ses_123",
                "current_file_id": "sf_123",
                "presentation_type": "generated_deck",
                "title": "Quarterly Review",
                "status": "active",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "2026-04-24T12:05:00Z",
                "current_file": {
                    "id": "sf_123",
                    "kind": "presentation_revision",
                    "file_type": "pptx",
                    "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    "title": "Quarterly Review v1",
                    "original_filename": "quarterly_review.pptx",
                    "checksum_sha256": "abc123",
                    "size_bytes": 2048,
                    "created_at": "2026-04-24T12:00:00Z",
                    "updated_at": "2026-04-24T12:00:00Z",
                },
                "latest_version": {
                    "id": "presver_123",
                    "version_number": 1,
                    "file_id": "sf_123",
                    "parent_version_id": None,
                    "change_summary": "Initial version",
                    "created_at": "2026-04-24T12:00:00Z",
                },
            }
        }
    )
