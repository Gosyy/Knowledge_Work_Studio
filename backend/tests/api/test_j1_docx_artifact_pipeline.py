from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, is_zipfile

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


def test_j1_docx_edit_official_flow_returns_valid_docx_and_preserves_lineage(
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
        files={"file": ("draft.txt", b"# report\nStatus: draft", "text/plain")},
    )
    assert upload_response.status_code == 201
    upload_id = upload_response.json()["id"]

    task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "docx_edit"},
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
    assert payload["result_data"]["task_type"] == "docx_edit"
    assert payload["result_data"]["source_mode"] == "uploaded_source"
    artifact_id = payload["result_data"]["artifact_ids"][0]

    artifact_response = client.get(f"/artifacts/{artifact_id}")
    assert artifact_response.status_code == 200
    artifact = artifact_response.json()
    assert artifact["filename"] == "edited.docx"
    assert artifact["content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert artifact["size_bytes"] > 0

    download_response = client.get(f"/artifacts/{artifact_id}/download")
    assert download_response.status_code == 200
    docx_bytes = download_response.content
    assert is_zipfile(BytesIO(docx_bytes))

    with ZipFile(BytesIO(docx_bytes)) as docx:
        names = set(docx.namelist())
        assert "[Content_Types].xml" in names
        assert "_rels/.rels" in names
        assert "word/document.xml" in names
        document_xml = docx.read("word/document.xml").decode("utf-8")

    assert "Status: final" in document_xml

    artifact_sources = SqliteArtifactSourceRepository(repository_db_path).list_by_artifact(artifact_id)
    assert len(artifact_sources) == 1
    assert artifact_sources[0].source_file_id == upload_id
    assert artifact_sources[0].source_document_id is None
    assert artifact_sources[0].source_presentation_id is None
