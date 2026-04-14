from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app

client = TestClient(app)


def _reset_app_state() -> None:
    for attribute in (
        "app_container",
        "g1_execution_coordinator",
        "official_execution_coordinator",
    ):
        if hasattr(app.state, attribute):
            delattr(app.state, attribute)


def _configure_sqlite_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("REPOSITORY_DB_PATH", str(tmp_path / "repositories.sqlite3"))
    get_settings.cache_clear()
    _reset_app_state()


def test_g1_official_execution_flow_creates_task_result_and_artifact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_sqlite_test_env(monkeypatch, tmp_path)

    session_response = client.post("/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    create_task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "pdf_summary"},
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]
    assert create_task_response.json()["status"] == "pending"

    execute_response = client.post(
        f"/tasks/{task_id}/execute",
        json={"content": "Alpha. Beta. Gamma."},
    )
    assert execute_response.status_code == 200
    executed = execute_response.json()
    assert executed["id"] == task_id
    assert executed["status"] == "succeeded"
    assert executed["result_data"]["task_type"] == "pdf_summary"
    assert executed["result_data"]["output_text"] == "Alpha. Beta."
    artifact_ids = executed["result_data"]["artifact_ids"]
    assert len(artifact_ids) == 1

    get_task_response = client.get(f"/tasks/{task_id}")
    assert get_task_response.status_code == 200
    assert get_task_response.json()["status"] == "succeeded"
    assert get_task_response.json()["result_data"]["artifact_ids"] == artifact_ids

    get_artifact_response = client.get(f"/artifacts/{artifact_ids[0]}")
    assert get_artifact_response.status_code == 200
    artifact = get_artifact_response.json()
    assert artifact["task_id"] == task_id
    assert artifact["session_id"] == session_id
    assert artifact["filename"] == "summary.txt"
    assert artifact["content_type"] == "text/plain"
    assert artifact["size_bytes"] > 0

    download_response = client.get(f"/artifacts/{artifact_ids[0]}/download")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "text/plain; charset=utf-8"
    assert b"Alpha. Beta." in download_response.content


@pytest.mark.parametrize("task_type", ["slides_generate"])
def test_g1_official_execution_rejects_later_phase_or_fake_pipeline_task_types(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    task_type: str,
) -> None:
    _configure_sqlite_test_env(monkeypatch, tmp_path)

    session_response = client.post("/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    create_task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": task_type},
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    execute_response = client.post(
        f"/tasks/{task_id}/execute",
        json={"content": "Some content"},
    )
    assert execute_response.status_code == 409
    assert "not supported by the official G1 execution API yet" in execute_response.json()["detail"]

    get_task_response = client.get(f"/tasks/{task_id}")
    assert get_task_response.status_code == 200
    assert get_task_response.json()["status"] == "pending"
