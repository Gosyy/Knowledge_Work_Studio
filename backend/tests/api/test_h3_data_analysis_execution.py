from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app
from backend.app.repositories import SqliteExecutionRunRepository

client = TestClient(app)


def _reset_app_state() -> None:
    for attribute in (
        "app_container",
        "g1_execution_coordinator",
        "official_execution_coordinator",
    ):
        if hasattr(app.state, attribute):
            delattr(app.state, attribute)


def _configure_sqlite_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> str:
    repository_db_path = str(tmp_path / "repositories.sqlite3")
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("REPOSITORY_DB_PATH", repository_db_path)
    get_settings.cache_clear()
    _reset_app_state()
    return repository_db_path


def test_h3_data_analysis_uses_real_engine_and_creates_result_artifact_and_trace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)

    session_response = client.post("/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "data_analysis"},
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    execute_response = client.post(
        f"/tasks/{task_id}/execute",
        json={"content": "col_a,col_b\n1,2\n3,4\n5,6"},
    )
    assert execute_response.status_code == 200
    payload = execute_response.json()

    assert payload["status"] == "succeeded"
    assert payload["result_data"]["task_type"] == "data_analysis"
    assert "Rows: 3" in payload["result_data"]["output_text"]
    assert "Columns: 2" in payload["result_data"]["output_text"]
    assert "Numeric cells: 6" in payload["result_data"]["output_text"]

    artifact_id = payload["result_data"]["artifact_ids"][0]
    artifact_response = client.get(f"/artifacts/{artifact_id}")
    assert artifact_response.status_code == 200
    artifact = artifact_response.json()
    assert artifact["filename"] == "analysis.txt"
    assert artifact["content_type"] == "text/plain"
    assert artifact["size_bytes"] > 0

    download_response = client.get(f"/artifacts/{artifact_id}/download")
    assert download_response.status_code == 200
    assert b"Rows: 3" in download_response.content

    execution_run_id = payload["result_data"]["execution_run_id"]
    execution_runs = SqliteExecutionRunRepository(repository_db_path).list_by_task(task_id)
    assert len(execution_runs) == 1
    assert execution_runs[0].id == execution_run_id
    assert execution_runs[0].task_id == task_id
    assert execution_runs[0].status == "succeeded"
    assert execution_runs[0].result_json is not None
    assert execution_runs[0].result_json["task_type"] == "data_analysis"
