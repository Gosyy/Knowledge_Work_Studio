from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class User:
    """Application user identity.

    M1 creates the user/auth foundation only. Resource ownership enforcement is
    intentionally left to M2.
    """

    id: str
    email: str
    password_hash: str
    display_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        normalized_email = self.email.strip().lower()
        if not self.id.strip():
            raise ValueError("User id must not be empty.")
        if not normalized_email:
            raise ValueError("User email must not be empty.")
        if not self.password_hash.strip():
            raise ValueError("User password_hash must not be empty.")
        object.__setattr__(self, "email", normalized_email)
