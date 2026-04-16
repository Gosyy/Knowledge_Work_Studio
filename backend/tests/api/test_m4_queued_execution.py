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
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("REPOSITORY_DB_PATH", str(tmp_path / "repositories.sqlite3"))
    get_settings.cache_clear()
    _reset_app_state()


def test_m4_enqueue_then_worker_run_processes_real_execution(monkeypatch, tmp_path: Path) -> None:
    _configure(monkeypatch, tmp_path)
    headers = {"X-User-Id": "alice"}

    session_id = client.post("/sessions", json={}, headers=headers).json()["id"]
    task_id = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "pdf_summary"},
        headers=headers,
    ).json()["id"]

    enqueue_response = client.post(
        f"/tasks/{task_id}/enqueue",
        json={"content": "Summarize queued execution honestly."},
        headers=headers,
    )
    assert enqueue_response.status_code == 202
    job = enqueue_response.json()
    assert job["status"] == "queued"
    assert job["task_id"] == task_id

    run_response = client.post(f"/task-jobs/{job['id']}/run", headers=headers)
    assert run_response.status_code == 200
    completed_job = run_response.json()
    assert completed_job["status"] == "succeeded"
    assert completed_job["result_task_id"] == task_id
    assert completed_job["completed_at"] is not None

    task = client.get(f"/tasks/{task_id}", headers=headers).json()
    assert task["status"] == "succeeded"
    assert task["result_data"]["queued_job_id"] == job["id"]
    assert task["result_data"]["artifact_ids"]

    artifact_id = task["result_data"]["artifact_ids"][0]
    assert client.get(f"/artifacts/{artifact_id}", headers=headers).status_code == 200


def test_m4_cross_user_cannot_read_or_run_queued_job(monkeypatch, tmp_path: Path) -> None:
    _configure(monkeypatch, tmp_path)
    alice = {"X-User-Id": "alice"}
    bob = {"X-User-Id": "bob"}

    session_id = client.post("/sessions", json={}, headers=alice).json()["id"]
    task_id = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "pdf_summary"},
        headers=alice,
    ).json()["id"]
    job_id = client.post(
        f"/tasks/{task_id}/enqueue",
        json={"content": "Only Alice may run this."},
        headers=alice,
    ).json()["id"]

    assert client.get(f"/task-jobs/{job_id}", headers=bob).status_code == 404
    assert client.post(f"/task-jobs/{job_id}/run", headers=bob).status_code == 404

    task = client.get(f"/tasks/{task_id}", headers=alice).json()
    assert task["status"] == "pending"
