from pathlib import Path


def test_m3_alembic_config_points_to_migrations_directory() -> None:
    config = Path("alembic.ini").read_text(encoding="utf-8")

    assert "script_location = migrations" in config
    assert "prepend_sys_path = ." in config


def test_m3_alembic_env_uses_project_settings_and_rejects_non_postgres() -> None:
    env_py = Path("migrations/env.py").read_text(encoding="utf-8")

    assert "from backend.app.core.config import Settings" in env_py
    assert "settings.database_url" in env_py
    assert "Alembic migrations are the production Postgres migration path only" in env_py
    assert "sqlite" not in env_py.lower()


def test_m3_initial_migration_represents_current_approved_schema() -> None:
    migration = Path("migrations/versions/0001_current_approved_schema.py").read_text(encoding="utf-8")

    expected_tables = [
        "users",
        "sessions",
        "tasks",
        "artifacts",
        "uploaded_files",
        "stored_files",
        "documents",
        "document_versions",
        "presentations",
        "presentation_versions",
        "artifact_sources",
        "derived_contents",
    ]

    for table_name in expected_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in migration

    assert "owner_user_id TEXT NOT NULL DEFAULT 'user_local_default'" in migration
    assert "CREATE UNIQUE INDEX IF NOT EXISTS uq_stored_files_storage_backend_key" in migration
    assert "down_revision: Union[str, None] = None" in migration


def test_m3_bootstrap_compatibility_is_documented_and_preserved() -> None:
    docs = Path("docs/deployment/migrations.md").read_text(encoding="utf-8")
    bootstrap = Path("backend/app/integrations/database/bootstrap.py").read_text(encoding="utf-8")

    assert "Alembic manages the Postgres schema only" in docs
    assert "Bootstrap compatibility" in docs
    assert "def initialize_database" in bootstrap
    assert "apply_postgres_baseline" in bootstrap


def test_m3_requirements_include_alembic() -> None:
    requirements = Path("requirements.txt").read_text(encoding="utf-8").lower()

    assert "alembic" in requirements
