import logging
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app

client = TestClient(app)


def _reset_app_state() -> None:
    for attr in (
        "app_container",
        "official_execution_coordinator",
        "task_queue_service",
        "llm_provider",
        "llm_text_service",
    ):
        if hasattr(app.state, attr):
            delattr(app.state, attr)


def _configure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("REPOSITORY_DB_PATH", str(tmp_path / "repositories.sqlite3"))
    get_settings.cache_clear()
    _reset_app_state()


def test_m7_request_id_is_echoed_and_logged(monkeypatch, tmp_path: Path, caplog) -> None:
    _configure(monkeypatch, tmp_path)
    caplog.set_level(logging.INFO)

    response = client.get("/health", headers={"X-Request-ID": "req-explicit-1"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-explicit-1"
    assert any(record.message == "request_completed" for record in caplog.records)
    assert any(getattr(record, "request_id", None) == "req-explicit-1" for record in caplog.records)


def test_m7_request_id_is_generated_when_missing(monkeypatch, tmp_path: Path, caplog) -> None:
    _configure(monkeypatch, tmp_path)
    caplog.set_level(logging.INFO)

    response = client.get("/health")

    assert response.status_code == 200
    request_id = response.headers["X-Request-ID"]
    assert request_id.startswith("req_")
    assert any(record.message == "request_started" for record in caplog.records)
    assert any(getattr(record, "request_id", None) == request_id for record in caplog.records)


def test_m7_task_execution_logs_task_correlation(monkeypatch, tmp_path: Path, caplog) -> None:
    _configure(monkeypatch, tmp_path)
    caplog.set_level(logging.INFO)
    headers = {"X-User-Id": "alice", "X-Request-ID": "req-task-1"}

    session_id = client.post("/sessions", json={}, headers=headers).json()["id"]
    task_id = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "pdf_summary"},
        headers=headers,
    ).json()["id"]

    response = client.post(
        f"/tasks/{task_id}/execute",
        json={"content": "Summarize this document safely."},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"

    messages = {record.message for record in caplog.records}
    assert "task_execution_started" in messages
    assert "task_execution_succeeded" in messages
    assert any(getattr(record, "task_id", None) == task_id for record in caplog.records)
    assert any(getattr(record, "request_id", None) == "req-task-1" for record in caplog.records)


def test_m7_readiness_logging_avoids_secret_echo(monkeypatch, tmp_path: Path, caplog) -> None:
    _configure(monkeypatch, tmp_path)
    caplog.set_level(logging.INFO)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEPLOYMENT_MODE", "offline_intranet")
    monkeypatch.setenv("SECRET_KEY", "super-secret-key-value")
    monkeypatch.setenv("METADATA_BACKEND", "postgres")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "false")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://kw:kw@postgres.internal:5432/kw")
    monkeypatch.setenv("STORAGE_BACKEND", "minio")
    monkeypatch.setenv("STORAGE_ENDPOINT", "")
    monkeypatch.setenv("STORAGE_BUCKET", "kw")
    monkeypatch.setenv("STORAGE_ACCESS_KEY", "access-key")
    monkeypatch.setenv("STORAGE_SECRET_KEY", "very-secret-storage-key")
    monkeypatch.setenv("LLM_PROVIDER", "gigachat")
    monkeypatch.setenv("GIGACHAT_API_BASE_URL", "https://gigachat-gateway.internal.example/api/v1")
    monkeypatch.setenv("GIGACHAT_AUTH_URL", "https://gigachat-gateway.internal.example/oauth")
    monkeypatch.setenv("GIGACHAT_CLIENT_ID", "client-id")
    monkeypatch.setenv("GIGACHAT_CLIENT_SECRET", "super-sensitive-client-secret")
    get_settings.cache_clear()

    response = client.get("/ready", headers={"X-Request-ID": "req-ready-1"})

    assert response.status_code == 503
    assert any(record.message == "readiness_evaluated" for record in caplog.records)
    all_messages = " ".join(record.getMessage() for record in caplog.records)
    assert "very-secret-storage-key" not in all_messages
    assert "super-sensitive-client-secret" not in all_messages
