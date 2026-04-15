from pathlib import Path


def test_m1_sqlite_baseline_contains_users_table() -> None:
    baseline = Path("scripts/migrations/0001_repository_baseline.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS users" in baseline
    assert "email TEXT NOT NULL UNIQUE" in baseline
    assert "password_hash TEXT NOT NULL" in baseline


def test_m1_postgres_bootstrap_contains_users_table() -> None:
    bootstrap = Path("backend/app/integrations/database/bootstrap.py").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS users" in bootstrap
    assert "email TEXT NOT NULL UNIQUE" in bootstrap
    assert "password_hash TEXT NOT NULL" in bootstrap
