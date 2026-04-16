from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


DEFAULT_OWNER_USER_ID = "user_local_default"


@dataclass(frozen=True)
class UploadedFile:
    id: str
    session_id: str
    original_filename: str
    content_type: str
    size_bytes: int
    owner_user_id: str = DEFAULT_OWNER_USER_ID
    storage_backend: str = "local"
    storage_key: str = ""
    storage_uri: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
