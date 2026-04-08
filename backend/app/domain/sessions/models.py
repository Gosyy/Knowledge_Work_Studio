from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Session:
    id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
