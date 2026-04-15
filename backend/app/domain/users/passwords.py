from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from typing import Protocol


class PasswordHasher(Protocol):
    def hash_password(self, password: str) -> str: ...

    def verify_password(self, password: str, password_hash: str) -> bool: ...


class Pbkdf2PasswordHasher:
    """Dependency-free PBKDF2 password hasher for the M1 auth foundation."""

    algorithm = "pbkdf2_sha256"

    def __init__(self, *, iterations: int = 390_000, salt_bytes: int = 16) -> None:
        if iterations < 100_000:
            raise ValueError("PBKDF2 iterations must be at least 100000.")
        if salt_bytes < 16:
            raise ValueError("Salt must be at least 16 bytes.")
        self._iterations = iterations
        self._salt_bytes = salt_bytes

    def hash_password(self, password: str) -> str:
        if not password:
            raise ValueError("Password must not be empty.")
        salt = secrets.token_bytes(self._salt_bytes)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self._iterations,
        )
        salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii")
        digest_b64 = base64.urlsafe_b64encode(digest).decode("ascii")
        return f"{self.algorithm}${self._iterations}${salt_b64}${digest_b64}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, iterations_raw, salt_b64, expected_b64 = password_hash.split("$", 3)
            iterations = int(iterations_raw)
        except (ValueError, TypeError):
            return False

        if algorithm != self.algorithm or iterations < 100_000:
            return False

        try:
            salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
            expected = base64.urlsafe_b64decode(expected_b64.encode("ascii"))
        except Exception:
            return False

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual, expected)
