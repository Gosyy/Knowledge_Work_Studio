from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.domain import Artifact
from backend.app.main import app


client = TestClient(app)


def _reset_app_container() -> None:
    if hasattr(app.state, "app_container"):
        delattr(app.state, "app_container")


def _configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "metadata.sqlite3"))
    monkeypatch.setenv("SQLITE_MIGRATIONS_DIR", str(Path(__file__).resolve().parents[3] / "scripts" / "migrations"))
    get_settings.cache_clear()
    _reset_app_container()


def test_issue_007_get_list_and_download_artifacts(monkeypatch, tmp_path: Path) -> None:
    _configure_test_env(monkeypatch, tmp_path)

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
    assert artifact_path.exists()

    metadata_resp = client.get(f"/artifacts/{artifact.id}")
    assert metadata_resp.status_code == 200
    assert metadata_resp.json()["id"] == artifact.id

    list_resp = client.get(f"/sessions/{session_id}/artifacts")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert len(listed) == 1
    assert listed[0]["id"] == artifact.id
    assert listed[0]["storage_path"] == artifact.storage_path

    download_resp = client.get(f"/artifacts/{artifact.id}/download")
    assert download_resp.status_code == 200
    assert download_resp.content.startswith(b"KW Studio artifact placeholder")
    assert download_resp.headers["content-type"] == artifact.content_type
    assert 'attachment; filename="edited.docx"' in download_resp.headers["content-disposition"]


def test_issue_007_download_not_found_paths(monkeypatch, tmp_path: Path) -> None:
    _configure_test_env(monkeypatch, tmp_path)

    missing_artifact = client.get("/artifacts/art_missing/download")
    assert missing_artifact.status_code == 404

    session_resp = client.post("/sessions", json={})
    session_id = session_resp.json()["id"]
    task_resp = client.post("/tasks", json={"session_id": session_id, "task_type": "docx_edit"})
    task_id = task_resp.json()["id"]

    orphan_artifact = app.state.app_container.artifact_service.artifacts.create(
        Artifact(
            id="art_orphan",
            session_id=session_id,
            task_id=task_id,
            filename="missing.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            storage_path=str(tmp_path / "artifacts" / "missing.docx"),
            size_bytes=10,
            created_at=datetime.now(timezone.utc),
        )
    )

    missing_file = client.get(f"/artifacts/{orphan_artifact.id}/download")
    assert missing_file.status_code == 404

    download_resp = client.get(f"/artifacts/{artifact.id}/download")
    assert download_resp.status_code == 200
    assert download_resp.content.startswith(b"KW Studio artifact placeholder")
    assert download_resp.headers["content-type"] == artifact.content_type
    assert 'attachment; filename="edited.docx"' in download_resp.headers["content-disposition"]


def test_issue_007_download_not_found_paths(monkeypatch, tmp_path: Path) -> None:
    _configure_test_env(monkeypatch, tmp_path)

    missing_artifact = client.get("/artifacts/art_missing/download")
    assert missing_artifact.status_code == 404

    session_resp = client.post("/sessions", json={})
    session_id = session_resp.json()["id"]
    task_resp = client.post("/tasks", json={"session_id": session_id, "task_type": "docx_edit"})
    task_id = task_resp.json()["id"]

    orphan_artifact = app.state.app_container.artifact_service.artifacts.create(
        Artifact(
            id="art_orphan",
            session_id=session_id,
            task_id=task_id,
            filename="missing.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            storage_path=str(tmp_path / "artifacts" / "missing.docx"),
            size_bytes=10,
            created_at=datetime.now(timezone.utc),
        )
    )

    missing_file = client.get(f"/artifacts/{orphan_artifact.id}/download")
    assert missing_file.status_code == 404


def test_issue_007_artifact_endpoints_not_found(monkeypatch, tmp_path: Path) -> None:
    _configure_test_env(monkeypatch, tmp_path)

    missing_artifact = client.get("/artifacts/art_missing")
    assert missing_artifact.status_code == 404

    missing_session = client.get("/sessions/ses_missing/artifacts")
    assert missing_session.status_code == 404
