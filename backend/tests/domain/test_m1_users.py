import pytest

from backend.app.domain import User
from backend.app.domain.users import Pbkdf2PasswordHasher


def test_m1_user_model_normalizes_email_and_requires_password_hash() -> None:
    user = User(
        id="user_1",
        email="  Admin@Example.COM  ",
        password_hash="hashed-password",
        display_name="Admin",
    )

    assert user.email == "admin@example.com"
    assert user.display_name == "Admin"
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.created_at.tzinfo is not None
    assert user.updated_at.tzinfo is not None


def test_m1_user_model_rejects_missing_password_hash() -> None:
    with pytest.raises(ValueError, match="password_hash"):
        User(id="user_1", email="admin@example.com", password_hash="")


def test_m1_password_hasher_never_returns_plaintext_and_verifies() -> None:
    hasher = Pbkdf2PasswordHasher(iterations=100_000)

    password_hash = hasher.hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert password_hash.startswith("pbkdf2_sha256$")
    assert hasher.verify_password("correct horse battery staple", password_hash) is True
    assert hasher.verify_password("wrong password", password_hash) is False
    assert hasher.verify_password("correct horse battery staple", "invalid-format") is False
