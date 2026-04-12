from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Artifact:
    id: str
    session_id: str
    task_id: str
    filename: str
    content_type: str
    storage_backend: str = "local"
    storage_key: str = ""
    storage_uri: str = ""
    size_bytes: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
