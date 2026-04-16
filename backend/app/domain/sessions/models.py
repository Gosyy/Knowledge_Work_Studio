from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


DEFAULT_OWNER_USER_ID = "user_local_default"


@dataclass(frozen=True)
class Session:
    id: str
    owner_user_id: str = DEFAULT_OWNER_USER_ID
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
