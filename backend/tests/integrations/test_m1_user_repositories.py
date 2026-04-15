from pathlib import Path

from backend.app.domain import User
from backend.app.repositories import PostgresUserRepository, SqliteUserRepository, UserRepository


def test_m1_sqlite_user_repository_persists_users_across_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "users.sqlite3"
    writer: UserRepository = SqliteUserRepository(str(db_path))

    user = User(
        id="user_1",
        email="Admin@Example.COM",
        password_hash="pbkdf2_sha256$100000$salt$hash",
        display_name="Admin",
    )

    writer.create(user)

    reader = SqliteUserRepository(str(db_path))
    assert reader.get("user_1") == user
    assert reader.get_by_email("admin@example.com") == user
    assert [item.id for item in reader.list()] == ["user_1"]


def test_m1_user_repository_exports_postgres_and_sqlite_implementations() -> None:
    assert PostgresUserRepository is not None
    assert SqliteUserRepository is not None
