from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app


client = TestClient(app)


def _reset_app_container() -> None:
    if hasattr(app.state, "app_container"):
        delattr(app.state, "app_container")


def test_issue_006_session_upload_task_flow(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "metadata.sqlite3"))
    monkeypatch.setenv("SQLITE_MIGRATIONS_DIR", str(Path(__file__).resolve().parents[3] / "scripts" / "migrations"))
    get_settings.cache_clear()
    _reset_app_container()

    session_response = client.post("/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    upload_response = client.post(
        "/uploads",
        data={"session_id": session_id},
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert upload_response.status_code == 201
    upload_body = upload_response.json()
    assert upload_body["session_id"] == session_id
    assert upload_body["original_filename"] == "notes.txt"
    assert upload_body["stored_filename"].startswith("upl_")

    task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "pdf_summary"},
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    get_task_response = client.get(f"/tasks/{task_id}")
    assert get_task_response.status_code == 200
    assert get_task_response.json()["status"] == "pending"

    get_session_response = client.get(f"/sessions/{session_id}")
    assert get_session_response.status_code == 200
    assert task_id in get_session_response.json()["task_ids"]
    assert upload_body["id"] in get_session_response.json()["upload_file_ids"]


def test_issue_006_returns_404_for_missing_resources(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "metadata.sqlite3"))
    monkeypatch.setenv("SQLITE_MIGRATIONS_DIR", str(Path(__file__).resolve().parents[3] / "scripts" / "migrations"))
    get_settings.cache_clear()
    _reset_app_container()

    missing_task = client.get("/tasks/task_missing")
    assert missing_task.status_code == 404

    missing_session = client.get("/sessions/ses_missing")
    assert missing_session.status_code == 404
