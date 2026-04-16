from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app

client = TestClient(app)


def _reset_app_container() -> None:
    for attr in ("app_container", "official_execution_coordinator", "llm_provider", "llm_text_service"):
        if hasattr(app.state, attr):
            delattr(app.state, attr)


def _configure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("REPOSITORY_DB_PATH", str(tmp_path / "repositories.sqlite3"))
    get_settings.cache_clear()
    _reset_app_container()


def test_m2_cross_user_session_task_and_upload_access_is_denied(monkeypatch, tmp_path: Path) -> None:
    _configure(monkeypatch, tmp_path)
    alice = {"X-User-Id": "alice"}
    bob = {"X-User-Id": "bob"}

    session_response = client.post("/sessions", json={}, headers=alice)
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    assert client.get(f"/sessions/{session_id}", headers=bob).status_code == 404

    bob_task_response = client.post("/tasks", json={"session_id": session_id, "task_type": "pdf_summary"}, headers=bob)
    assert bob_task_response.status_code == 404

    upload_response = client.post(
        "/uploads",
        data={"session_id": session_id},
        files={"file": ("notes.txt", b"hello world", "text/plain")},
        headers=alice,
    )
    assert upload_response.status_code == 201
    upload_id = upload_response.json()["id"]

    bob_upload_response = client.post(
        "/uploads",
        data={"session_id": session_id},
        files={"file": ("other.txt", b"blocked", "text/plain")},
        headers=bob,
    )
    assert bob_upload_response.status_code == 404

    task_response = client.post("/tasks", json={"session_id": session_id, "task_type": "pdf_summary"}, headers=alice)
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]
    assert client.get(f"/tasks/{task_id}", headers=bob).status_code == 404

    bob_session_id = client.post("/sessions", json={}, headers=bob).json()["id"]
    bob_task = client.post("/tasks", json={"session_id": bob_session_id, "task_type": "pdf_summary"}, headers=bob).json()["id"]

    cross_upload_execute = client.post(f"/tasks/{bob_task}/execute", json={"uploaded_file_ids": [upload_id]}, headers=bob)
    assert cross_upload_execute.status_code == 404

    cross_stored_execute = client.post(f"/tasks/{bob_task}/execute", json={"stored_file_ids": [upload_id]}, headers=bob)
    assert cross_stored_execute.status_code == 404


def test_m2_cross_user_artifact_access_and_download_are_denied(monkeypatch, tmp_path: Path) -> None:
    _configure(monkeypatch, tmp_path)
    alice = {"X-User-Id": "alice"}
    bob = {"X-User-Id": "bob"}

    session_id = client.post("/sessions", json={}, headers=alice).json()["id"]
    task_id = client.post("/tasks", json={"session_id": session_id, "task_type": "pdf_summary"}, headers=alice).json()["id"]

    executed = client.post(f"/tasks/{task_id}/execute", json={"content": "Summarize this text."}, headers=alice)
    assert executed.status_code == 200
    artifact_id = executed.json()["result_data"]["artifact_ids"][0]

    assert client.get(f"/artifacts/{artifact_id}", headers=alice).status_code == 200
    assert client.get(f"/artifacts/{artifact_id}", headers=bob).status_code == 404
    assert client.get(f"/artifacts/{artifact_id}/download", headers=bob).status_code == 404
    assert client.get(f"/sessions/{session_id}/artifacts", headers=bob).status_code == 404
