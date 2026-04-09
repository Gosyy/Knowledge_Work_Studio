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
    storage_path: str | None = None
    size_bytes: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
