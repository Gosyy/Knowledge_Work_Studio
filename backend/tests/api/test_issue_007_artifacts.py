from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app


client = TestClient(app)


def _reset_app_container() -> None:
    if hasattr(app.state, "app_container"):
        delattr(app.state, "app_container")


def test_issue_007_get_and_list_artifacts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("REPOSITORY_DB_PATH", str(tmp_path / "repositories.sqlite3"))
    get_settings.cache_clear()
    _reset_app_container()

    session_resp = client.post("/sessions", json={})
    session_id = session_resp.json()["id"]

    task_resp = client.post("/tasks", json={"session_id": session_id, "task_type": "docx_edit"})
    task_id = task_resp.json()["id"]

    artifact = app.state.app_container.artifact_service.create_placeholder_artifact(
        session_id=session_id,
        task_id=task_id,
        filename="edited.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    get_resp = client.get(f"/artifacts/{artifact.id}")
    assert get_resp.status_code == 200
    get_payload = get_resp.json()
    assert get_payload["id"] == artifact.id
    assert get_payload["storage_backend"] == "local"
    assert get_payload["storage_key"].startswith(f"artifacts/{session_id}/{task_id}/{artifact.id}/")
    assert get_payload["storage_uri"] == f"local://{get_payload['storage_key']}"
    assert get_payload["size_bytes"] == 0

    list_resp = client.get(f"/sessions/{session_id}/artifacts")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert len(listed) == 1
    assert listed[0]["id"] == artifact.id
    assert listed[0]["storage_uri"] == f"local://{listed[0]['storage_key']}"


def test_issue_007_artifact_endpoints_not_found(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("REPOSITORY_DB_PATH", str(tmp_path / "repositories.sqlite3"))
    get_settings.cache_clear()
    _reset_app_container()

    missing_artifact = client.get("/artifacts/art_missing")
    assert missing_artifact.status_code == 404

    missing_session = client.get("/sessions/ses_missing/artifacts")
    assert missing_session.status_code == 404

    missing_download = client.get("/artifacts/art_missing/download")
    assert missing_download.status_code == 404


def test_issue_007_artifacts_persist_after_container_reset(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("REPOSITORY_DB_PATH", str(tmp_path / "repositories.sqlite3"))
    get_settings.cache_clear()
    _reset_app_container()

    session_resp = client.post("/sessions", json={})
    session_id = session_resp.json()["id"]

    task_resp = client.post("/tasks", json={"session_id": session_id, "task_type": "docx_edit"})
    task_id = task_resp.json()["id"]

    artifact = app.state.app_container.artifact_service.create_placeholder_artifact(
        session_id=session_id,
        task_id=task_id,
        filename="edited.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    _reset_app_container()

    get_resp = client.get(f"/artifacts/{artifact.id}")
    assert get_resp.status_code == 200
    payload = get_resp.json()
    assert payload["id"] == artifact.id
    assert payload["storage_key"].endswith(f"{artifact.id}-edited.docx")
    assert payload["size_bytes"] == 0


def test_issue_007_download_artifact_returns_file_content(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("REPOSITORY_DB_PATH", str(tmp_path / "repositories.sqlite3"))
    get_settings.cache_clear()
    _reset_app_container()

    session_resp = client.post("/sessions", json={})
    session_id = session_resp.json()["id"]
    task_resp = client.post("/tasks", json={"session_id": session_id, "task_type": "docx_edit"})
    task_id = task_resp.json()["id"]

    artifact = app.state.app_container.artifact_service.create_placeholder_artifact(
        session_id=session_id,
        task_id=task_id,
        filename="edited.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    app.state.app_container.artifact_service.storage.save_bytes(storage_key=artifact.storage_key, content=b"doc-bytes")

    download_resp = client.get(f"/artifacts/{artifact.id}/download")
    assert download_resp.status_code == 200
    assert download_resp.content == b"doc-bytes"
    assert (
        download_resp.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert "attachment; filename=\"edited.docx\"" in download_resp.headers["content-disposition"]
