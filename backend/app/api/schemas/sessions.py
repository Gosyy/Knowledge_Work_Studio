from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionCreateRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {}})


class SessionSchema(BaseModel):
    id: str
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ses_4f2b1c",
                "created_at": "2026-04-22T12:00:00Z",
            }
        }
    )


class SessionDetailSchema(SessionSchema):
    task_ids: list[str]
    upload_file_ids: list[str]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ses_4f2b1c",
                "created_at": "2026-04-22T12:00:00Z",
                "task_ids": ["task_71f0d3"],
                "upload_file_ids": ["upl_14be29"],
            }
        }
    )
