from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from backend.app.composition import build_storage
from backend.app.core.config import Settings, get_settings
from backend.app.deployment import build_deployment_readiness
from backend.app.integrations.file_storage import S3CompatibleFileStorage
from backend.app.main import app


def approved_settings(tmp_path: Path) -> Settings:
    return Settings(
        app_env="production",
        deployment_mode="offline_intranet",
        secret_key="super-secret-key-value",
        metadata_backend="postgres",
        sqlite_runtime_allowed=False,
        database_url="postgresql+psycopg://kw_studio:secret@postgres.internal:5432/kw_studio",
        storage_backend="local",
        storage_root=str(tmp_path / "storage"),
        uploads_dir=str(tmp_path / "storage" / "uploads"),
        artifacts_dir=str(tmp_path / "storage" / "artifacts"),
        temp_dir=str(tmp_path / "storage" / "temp"),
        llm_provider="gigachat",
        gigachat_api_base_url="https://gigachat-gateway.internal.example/api/v1",
        gigachat_auth_url="https://gigachat-gateway.internal.example/oauth",
        gigachat_client_id="client-id",
        gigachat_client_secret="client-secret",
    )


def test_l3_approved_offline_intranet_profile_is_ready(tmp_path: Path) -> None:
    readiness = build_deployment_readiness(approved_settings(tmp_path))

    assert readiness.status == "ready"
    assert readiness.deployment_mode == "offline_intranet"
    assert readiness.metadata_backend == "postgres"
    assert readiness.storage_backend == "local"
    assert readiness.llm_provider == "gigachat"
    assert readiness.checks["postgres_metadata_truth"] is True
    assert readiness.checks["llm_provider_gigachat_only"] is True
    assert readiness.errors == ()


def test_l3_rejects_hidden_sqlite_and_fake_provider(tmp_path: Path) -> None:
    settings = approved_settings(tmp_path).model_copy(
        update={
            "metadata_backend": "sqlite",
            "sqlite_runtime_allowed": True,
            "llm_provider": "fake",
            "secret_key": "change-me",
        }
    )

    readiness = build_deployment_readiness(settings)

    assert readiness.status == "not_ready"
    assert readiness.checks["postgres_metadata_truth"] is False
    assert readiness.checks["sqlite_not_runtime_truth"] is False
    assert readiness.checks["llm_provider_gigachat_only"] is False
    assert any("METADATA_BACKEND must be postgres" in error for error in readiness.errors)
    assert any("LLM_PROVIDER must be gigachat" in error for error in readiness.errors)


def test_l3_ready_endpoint_reports_approved_profile(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEPLOYMENT_MODE", "offline_intranet")
    monkeypatch.setenv("SECRET_KEY", "super-secret-key-value")
    monkeypatch.setenv("METADATA_BACKEND", "postgres")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "false")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://kw_studio:secret@postgres.internal:5432/kw_studio",
    )
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "storage" / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "storage" / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "storage" / "temp"))
    monkeypatch.setenv("LLM_PROVIDER", "gigachat")
    monkeypatch.setenv("GIGACHAT_API_BASE_URL", "https://gigachat-gateway.internal.example/api/v1")
    monkeypatch.setenv("GIGACHAT_AUTH_URL", "https://gigachat-gateway.internal.example/oauth")
    monkeypatch.setenv("GIGACHAT_CLIENT_ID", "client-id")
    monkeypatch.setenv("GIGACHAT_CLIENT_SECRET", "client-secret")
    get_settings.cache_clear()

    response = TestClient(app).get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["deployment_mode"] == "offline_intranet"
    assert payload["metadata_backend"] == "postgres"
    assert payload["llm_provider"] == "gigachat"


def test_l3_remote_storage_missing_config_fails_readiness(tmp_path: Path) -> None:
    settings = approved_settings(tmp_path).model_copy(
        update={
            "storage_backend": "minio",
            "storage_root": "",
        }
    )

    readiness = build_deployment_readiness(settings)

    assert readiness.status == "not_ready"
    assert readiness.checks["storage_configured"] is False
    assert any("Storage backend settings are incomplete." in error for error in readiness.errors)


def test_l3_s3_compatible_storage_uses_real_adapter_path(monkeypatch, tmp_path: Path) -> None:
    settings = approved_settings(tmp_path).model_copy(
        update={
            "storage_backend": "minio",
            "storage_endpoint": "https://minio.internal.example:9000",
            "storage_bucket": "kw-studio",
            "storage_access_key": "access",
            "storage_secret_key": "secret",
            "storage_addressing_style": "path",
        }
    )

    readiness = build_deployment_readiness(settings)
    assert readiness.checks["storage_configured"] is True

    monkeypatch.setattr("backend.app.integrations.file_storage.s3.build_s3_client", lambda **kwargs: object())

    storage = build_storage(settings)

    assert isinstance(storage, S3CompatibleFileStorage)
    assert storage.backend_name == "minio"
    assert storage.make_uri(storage_key="uploads/ses_1/upl_1.txt") == "minio://kw-studio/uploads/ses_1/upl_1.txt"


def test_l3_invalid_storage_addressing_style_fails_readiness(tmp_path: Path) -> None:
    settings = approved_settings(tmp_path).model_copy(
        update={
            "storage_backend": "s3",
            "storage_endpoint": "https://s3.internal.example",
            "storage_bucket": "kw-studio",
            "storage_access_key": "access",
            "storage_secret_key": "secret",
            "storage_addressing_style": "broken",
        }
    )

    readiness = build_deployment_readiness(settings)

    assert readiness.status == "not_ready"
    assert readiness.checks["storage_addressing_style_supported"] is False
    assert any("STORAGE_ADDRESSING_STYLE must be one of" in error for error in readiness.errors)
