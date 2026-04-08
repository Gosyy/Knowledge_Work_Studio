from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class UploadedFile:
    id: str
    session_id: str
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
