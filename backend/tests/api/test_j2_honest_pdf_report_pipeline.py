from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app
from backend.app.repositories.sqlite import SqliteArtifactSourceRepository

client = TestClient(app)


def _reset_app_state() -> None:
    for attribute in (
        "app_container",
        "g1_execution_coordinator",
        "official_execution_coordinator",
        "llm_provider",
        "llm_text_service",
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


def test_j2_pdf_summary_official_flow_returns_honest_text_report_and_preserves_lineage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)

    session_response = client.post("/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    upload_response = client.post(
        "/uploads",
        data={"session_id": session_id},
        files={
            "file": (
                "source.txt",
                b"First finding is stable. Second finding requires follow-up. Third finding is optional.",
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 201
    upload_id = upload_response.json()["id"]

    task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "pdf_summary"},
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    execute_response = client.post(
        f"/tasks/{task_id}/execute",
        json={"uploaded_file_ids": [upload_id]},
    )
    assert execute_response.status_code == 200
    payload = execute_response.json()
    assert payload["status"] == "succeeded"
    assert payload["result_data"]["task_type"] == "pdf_summary"
    assert payload["result_data"]["source_mode"] == "uploaded_source"
    artifact_id = payload["result_data"]["artifact_ids"][0]

    artifact_response = client.get(f"/artifacts/{artifact_id}")
    assert artifact_response.status_code == 200
    artifact = artifact_response.json()
    assert artifact["filename"] == "summary.txt"
    assert artifact["content_type"] == "text/plain"
    assert artifact["size_bytes"] > 0

    download_response = client.get(f"/artifacts/{artifact_id}/download")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "text/plain; charset=utf-8"
    report_bytes = download_response.content
    assert report_bytes.startswith(b"Summary Report\n")
    assert b"Format: text/plain" in report_bytes
    assert b"not a PDF binary" in report_bytes
    assert not report_bytes.startswith(b"%PDF")

    artifact_sources = SqliteArtifactSourceRepository(repository_db_path).list_by_artifact(artifact_id)
    assert len(artifact_sources) == 1
    assert artifact_sources[0].source_file_id == upload_id
    assert artifact_sources[0].source_document_id is None
    assert artifact_sources[0].source_presentation_id is None
