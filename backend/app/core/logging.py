from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

_SENSITIVE_KEY_PARTS = (
    "SECRET",
    "PASSWORD",
    "TOKEN",
    "ACCESS_KEY",
    "API_KEY",
    "CLIENT_SECRET",
    "DATABASE_URL",
)


def is_sensitive_key(key: str) -> bool:
    normalized = key.upper()
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def redact_value(key: str, value: Any) -> Any:
    if not is_sensitive_key(key):
        return value
    if value is None:
        return "[unset]"
    if isinstance(value, str) and not value.strip():
        return "[unset]"
    return "[set]"


def redact_mapping(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: redact_value(key, value) for key, value in values.items()}


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


__all__ = ["get_logger", "is_sensitive_key", "redact_mapping", "redact_value"]
