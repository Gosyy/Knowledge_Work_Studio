from datetime import datetime

from pydantic import BaseModel


class SessionSchema(BaseModel):
    id: str
    created_at: datetime
