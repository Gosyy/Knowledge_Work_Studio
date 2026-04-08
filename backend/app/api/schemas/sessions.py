from datetime import datetime

from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    pass


class SessionSchema(BaseModel):
    id: str
    created_at: datetime


class SessionDetailSchema(SessionSchema):
    task_ids: list[str]
    upload_file_ids: list[str]
