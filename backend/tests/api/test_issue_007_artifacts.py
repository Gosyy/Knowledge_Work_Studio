from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app


client = TestClient(app)


def _reset_app_container() -> None:
    if hasattr(app.state, "app_container"):
        delattr(app.state, "app_container")


def test_issue_007_get_and_list_artifacts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "metadata.sqlite3"))
    monkeypatch.setenv("SQLITE_MIGRATIONS_DIR", str(Path(__file__).resolve().parents[3] / "scripts" / "migrations"))
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

    artifact_path = Path(artifact.storage_path or "")
    assert artifact.storage_path is not None
    assert artifact.size_bytes is not None
    assert artifact.size_bytes > 0
    assert artifact_path.exists()
    assert artifact_path.read_bytes().startswith(b"KW Studio artifact placeholder")

    get_resp = client.get(f"/artifacts/{artifact.id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == artifact.id
    assert get_resp.json()["storage_path"] == artifact.storage_path
    assert get_resp.json()["size_bytes"] == artifact.size_bytes

    list_resp = client.get(f"/sessions/{session_id}/artifacts")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert len(listed) == 1
    assert listed[0]["id"] == artifact.id
    assert listed[0]["storage_path"] == artifact.storage_path


def test_issue_007_artifact_endpoints_not_found(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "metadata.sqlite3"))
    monkeypatch.setenv("SQLITE_MIGRATIONS_DIR", str(Path(__file__).resolve().parents[3] / "scripts" / "migrations"))
    get_settings.cache_clear()
    _reset_app_container()

    missing_artifact = client.get("/artifacts/art_missing")
    assert missing_artifact.status_code == 404

    missing_session = client.get("/sessions/ses_missing/artifacts")
    assert missing_session.status_code == 404
