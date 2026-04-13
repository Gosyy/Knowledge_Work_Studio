from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.domain import Document, Presentation, StoredFile
from backend.app.main import app
from backend.app.repositories.sqlite import (
    SqliteArtifactSourceRepository,
    SqliteDocumentRepository,
    SqlitePresentationRepository,
    SqliteStoredFileRepository,
)

client = TestClient(app)


def _reset_app_state() -> None:
    for attribute in ("app_container", "g1_execution_coordinator"):
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


def test_g2_prompt_only_mode_remains_supported(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_sqlite_test_env(monkeypatch, tmp_path)

    session_response = client.post("/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "pdf_summary"},
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    execute_response = client.post(
        f"/tasks/{task_id}/execute",
        json={"content": "Alpha. Beta. Gamma."},
    )
    assert execute_response.status_code == 200
    payload = execute_response.json()

    assert payload["status"] == "succeeded"
    assert payload["result_data"]["source_mode"] == "prompt_only"
    assert payload["result_data"]["source_refs"] == []


def test_g2_uploaded_source_mode_persists_artifact_lineage(
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
        files={"file": ("notes.txt", b"Alpha. Beta. Gamma.", "text/plain")},
    )
    assert upload_response.status_code == 201
    upload_id = upload_response.json()["id"]

    stored_files = SqliteStoredFileRepository(repository_db_path)
    assert stored_files.get(upload_id) is not None

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
    assert payload["result_data"]["source_mode"] == "uploaded_source"
    assert payload["result_data"]["source_refs"] == [
        {"kind": "uploaded_file", "source_id": upload_id, "role": "primary_source"}
    ]

    artifact_id = payload["result_data"]["artifact_ids"][0]
    artifact_sources = SqliteArtifactSourceRepository(repository_db_path).list_by_artifact(artifact_id)
    assert len(artifact_sources) == 1
    assert artifact_sources[0].source_file_id == upload_id
    assert artifact_sources[0].source_document_id is None
    assert artifact_sources[0].source_presentation_id is None


@pytest.mark.parametrize(
    ("source_kind", "request_payload_builder"),
    [
        ("stored_file", lambda source_id: {"stored_file_ids": [source_id]}),
        ("document", lambda source_id: {"document_ids": [source_id]}),
        ("presentation", lambda source_id: {"presentation_ids": [source_id]}),
    ],
)
def test_g2_stored_source_modes_use_real_registered_sources(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    source_kind: str,
    request_payload_builder,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)

    session_response = client.post("/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    # Build the app container once so storage paths are initialized from the test env.
    task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "pdf_summary"},
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    storage = app.state.app_container.task_source_service.storage
    stored_files = SqliteStoredFileRepository(repository_db_path)
    documents = SqliteDocumentRepository(repository_db_path)
    presentations = SqlitePresentationRepository(repository_db_path)

    stored_file_id = f"sf_{source_kind}"
    storage_key = f"stored/{session_id}/{stored_file_id}/source.txt"
    storage_uri = storage.save_bytes(
        storage_key=storage_key,
        content=b"Alpha. Beta. Gamma.",
    )
    stored_files.create(
        StoredFile(
            id=stored_file_id,
            session_id=session_id,
            task_id=None,
            kind="uploaded_source",
            file_type="txt",
            mime_type="text/plain",
            title=f"{source_kind} source",
            original_filename="source.txt",
            storage_backend=storage.backend_name,
            storage_key=storage_key,
            storage_uri=storage_uri,
            checksum_sha256=None,
            size_bytes=len(b"Alpha. Beta. Gamma."),
        )
    )

    source_id = stored_file_id
    if source_kind == "document":
        source_id = "doc_g2"
        documents.create(
            Document(
                id=source_id,
                session_id=session_id,
                current_file_id=stored_file_id,
                document_type="summary",
                title="Document source",
            )
        )
    elif source_kind == "presentation":
        source_id = "pres_g2"
        presentations.create(
            Presentation(
                id=source_id,
                session_id=session_id,
                current_file_id=stored_file_id,
                presentation_type="status_update",
                title="Presentation source",
            )
        )

    execute_response = client.post(
        f"/tasks/{task_id}/execute",
        json=request_payload_builder(source_id),
    )
    assert execute_response.status_code == 200
    payload = execute_response.json()

    assert payload["status"] == "succeeded"
    assert payload["result_data"]["source_mode"] == "stored_source"
    assert len(payload["result_data"]["source_refs"]) == 1

    artifact_id = payload["result_data"]["artifact_ids"][0]
    artifact_sources = SqliteArtifactSourceRepository(repository_db_path).list_by_artifact(artifact_id)
    assert len(artifact_sources) == 1

    artifact_source = artifact_sources[0]
    if source_kind == "stored_file":
        assert artifact_source.source_file_id == source_id
        assert artifact_source.source_document_id is None
        assert artifact_source.source_presentation_id is None
    elif source_kind == "document":
        assert artifact_source.source_file_id is None
        assert artifact_source.source_document_id == source_id
        assert artifact_source.source_presentation_id is None
    else:
        assert artifact_source.source_file_id is None
        assert artifact_source.source_document_id is None
        assert artifact_source.source_presentation_id == source_id
