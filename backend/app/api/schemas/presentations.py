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


from datetime import datetime as _datetime_for_api_v1
from typing import Any, Literal

from pydantic import Field


class PresentationApiCreateRequestSchema(BaseModel):
    """API-first presentation creation contract for KR-7C."""

    session_id: str | None = None
    title: str | None = None
    objective: str = Field(min_length=1)
    audience: str | None = None
    scenario: str | None = None
    language: str = "ru"
    slide_count: int | None = Field(default=None, ge=1, le=100)
    source_ids: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class PresentationApiSourceAttachRequestSchema(BaseModel):
    source_file_ids: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
    presentation_ids: list[str] = Field(default_factory=list)
    role: str = "primary_source"

    model_config = ConfigDict(extra="forbid")


class PresentationApiSourceRefSchema(BaseModel):
    source_id: str
    source_type: Literal["uploaded_file", "stored_file", "document", "presentation"]
    role: str
    title: str | None = None
    file_type: str | None = None
    mime_type: str | None = None
    checksum_sha256: str | None = None
    size_bytes: int | None = None
    extraction_status: Literal["not_started", "pending", "ready", "unsupported", "missing"]
    source_file_id: str | None = None
    source_document_id: str | None = None
    source_presentation_id: str | None = None
    provenance_ref: str | None = None

    model_config = ConfigDict(extra="forbid")


class PresentationApiSourcesResponseSchema(BaseModel):
    api_version: str
    presentation_id: str
    snapshot_id: str
    presentation_version_id: str | None
    ir_schema_version: str
    storage_format: Literal["presentation_ir", "legacy_plan_snapshot"]
    version_number: int | None = None
    attachment_contract_version: str
    extraction_runtime_implemented: bool = False
    sources: list[PresentationApiSourceRefSchema]

    model_config = ConfigDict(extra="forbid")


class PresentationApiPlanRequestSchema(BaseModel):
    objective: str | None = None
    force_replan: bool = False
    source_ids: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class PresentationApiSlidePatchRequestSchema(BaseModel):
    title: str | None = None
    takeaway: str | None = None
    content: dict[str, Any] = Field(default_factory=dict)
    change_summary: str | None = None

    model_config = ConfigDict(extra="forbid")


class PresentationApiRenderRequestSchema(BaseModel):
    format: Literal["pptx", "pdf", "png"] = "pptx"
    quality_gate: bool = True

    model_config = ConfigDict(extra="forbid")


class PresentationApiContractStatusSchema(BaseModel):
    api_version: str = "presentation_api.v1"
    status: Literal["not_implemented"] = "not_implemented"
    phase: str = "KR-7C"
    message: str = "Endpoint contract is declared; runtime implementation belongs to a later KR-7C subphase."

    model_config = ConfigDict(extra="forbid")


class PresentationApiMetadataResponseSchema(BaseModel):
    api_version: str
    presentation: PresentationSchema

    model_config = ConfigDict(extra="forbid")


class PresentationApiPlanSnapshotResponseSchema(BaseModel):
    api_version: str
    snapshot_id: str
    presentation_id: str
    presentation_version_id: str | None
    created_from_task_id: str | None
    change_summary: str | None
    created_at: _datetime_for_api_v1
    schema_version: str
    ir_schema_version: str
    storage_format: Literal["presentation_ir", "legacy_plan_snapshot"]
    version_number: int | None = None
    plan: dict[str, Any]

    model_config = ConfigDict(extra="forbid")


class PresentationApiSlidesResponseSchema(BaseModel):
    api_version: str
    presentation_id: str
    snapshot_id: str
    presentation_version_id: str | None
    schema_version: str
    ir_schema_version: str
    storage_format: Literal["presentation_ir", "legacy_plan_snapshot"]
    version_number: int | None = None
    slides: list[dict[str, Any]]

    model_config = ConfigDict(extra="forbid")


class PresentationIRVersionSummarySchema(BaseModel):
    snapshot_id: str
    presentation_id: str
    presentation_version_id: str | None
    created_from_task_id: str | None
    change_summary: str | None
    created_at: _datetime_for_api_v1
    ir_schema_version: str
    storage_format: Literal["presentation_ir", "legacy_plan_snapshot"]
    version_number: int

    model_config = ConfigDict(extra="forbid")


class PresentationIRVersionsResponseSchema(BaseModel):
    api_version: str
    presentation_id: str
    ir_schema_version: str
    versions: list[PresentationIRVersionSummarySchema]

    model_config = ConfigDict(extra="forbid")


class PresentationIRSnapshotResponseSchema(BaseModel):
    api_version: str
    presentation_id: str
    snapshot_id: str
    presentation_version_id: str | None
    ir_schema_version: str
    storage_format: Literal["presentation_ir", "legacy_plan_snapshot"]
    version_number: int | None = None
    presentation_ir: dict[str, Any]

    model_config = ConfigDict(extra="forbid")
