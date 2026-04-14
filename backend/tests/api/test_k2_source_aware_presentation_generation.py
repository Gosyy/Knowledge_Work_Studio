from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, is_zipfile

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


def _create_session_and_slides_task() -> tuple[str, str]:
    session_response = client.post("/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "slides_generate"},
    )
    assert task_response.status_code == 201
    return session_id, task_response.json()["id"]


def _assert_valid_pptx(payload: bytes) -> None:
    assert is_zipfile(BytesIO(payload))
    with ZipFile(BytesIO(payload)) as pptx:
        names = set(pptx.namelist())
        assert "[Content_Types].xml" in names
        assert "_rels/.rels" in names
        assert "ppt/presentation.xml" in names
        assert "ppt/_rels/presentation.xml.rels" in names
        assert "ppt/slides/slide1.xml" in names
        assert "ppt/slides/_rels/slide1.xml.rels" in names
        assert "ppt/slideMasters/slideMaster1.xml" in names
        assert "ppt/slideLayouts/slideLayout1.xml" in names
        assert "ppt/theme/theme1.xml" in names
        assert not any(name.endswith(".txt") for name in names)


def _download_artifact(artifact_id: str) -> bytes:
    response = client.get(f"/artifacts/{artifact_id}/download")
    assert response.status_code == 200
    return response.content


def _create_stored_text_file(
    *,
    repository_db_path: str,
    session_id: str,
    stored_file_id: str,
    content: bytes,
    filename: str,
) -> StoredFile:
    storage = app.state.app_container.task_source_service.storage
    storage_key = f"stored/{session_id}/{stored_file_id}/{filename}"
    storage_uri = storage.save_bytes(storage_key=storage_key, content=content)
    stored_file = StoredFile(
        id=stored_file_id,
        session_id=session_id,
        task_id=None,
        kind="source",
        file_type="txt",
        mime_type="text/plain",
        title=filename,
        original_filename=filename,
        storage_backend=storage.backend_name,
        storage_key=storage_key,
        storage_uri=storage_uri,
        checksum_sha256=None,
        size_bytes=len(content),
    )
    SqliteStoredFileRepository(repository_db_path).create(stored_file)
    return stored_file


def test_k2_prompt_only_presentation_generation_is_outline_first_and_valid_pptx(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_sqlite_test_env(monkeypatch, tmp_path)
    _, task_id = _create_session_and_slides_task()

    response = client.post(
        f"/tasks/{task_id}/execute",
        json={"content": "Roadmap intro. Risks. Launch plan."},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "succeeded"
    assert payload["result_data"]["source_mode"] == "prompt_only"
    assert payload["result_data"]["source_refs"] == []
    assert payload["result_data"]["outline"][0]["title"].startswith("Slide 1:")
    assert payload["result_data"]["outline"][0]["bullets"] == ["Roadmap intro"]

    _assert_valid_pptx(_download_artifact(payload["result_data"]["artifact_ids"][0]))


def test_k2_uploaded_source_presentation_generation_records_provenance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id, task_id = _create_session_and_slides_task()

    upload_response = client.post(
        "/uploads",
        data={"session_id": session_id},
        files={"file": ("deck-source.txt", b"Uploaded opportunity. Uploaded plan.", "text/plain")},
    )
    assert upload_response.status_code == 201
    upload_id = upload_response.json()["id"]

    response = client.post(
        f"/tasks/{task_id}/execute",
        json={"uploaded_file_ids": [upload_id]},
    )
    assert response.status_code == 200
    payload = response.json()
    artifact_id = payload["result_data"]["artifact_ids"][0]

    assert payload["status"] == "succeeded"
    assert payload["result_data"]["source_mode"] == "uploaded_source"
    assert payload["result_data"]["source_refs"] == [
        {"kind": "uploaded_file", "source_id": upload_id, "role": "primary_source"}
    ]
    assert payload["result_data"]["outline"][0]["bullets"] == ["Uploaded opportunity"]

    sources = SqliteArtifactSourceRepository(repository_db_path).list_by_artifact(artifact_id)
    assert len(sources) == 1
    assert sources[0].source_file_id == upload_id
    assert sources[0].source_document_id is None
    assert sources[0].source_presentation_id is None
    _assert_valid_pptx(_download_artifact(artifact_id))


def test_k2_stored_file_document_and_presentation_sources_generate_valid_pptx_with_provenance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id, task_id = _create_session_and_slides_task()

    stored_file = _create_stored_text_file(
        repository_db_path=repository_db_path,
        session_id=session_id,
        stored_file_id="sf_k2_file",
        content=b"Stored file opportunity.",
        filename="stored-file.txt",
    )
    document_file = _create_stored_text_file(
        repository_db_path=repository_db_path,
        session_id=session_id,
        stored_file_id="sf_k2_document",
        content=b"Document source plan.",
        filename="document-source.txt",
    )
    presentation_file = _create_stored_text_file(
        repository_db_path=repository_db_path,
        session_id=session_id,
        stored_file_id="sf_k2_presentation",
        content=b"Presentation source risks.",
        filename="presentation-source.txt",
    )

    document_id = "doc_k2_source"
    presentation_id = "pres_k2_source"
    SqliteDocumentRepository(repository_db_path).create(
        Document(
            id=document_id,
            session_id=session_id,
            current_file_id=document_file.id,
            document_type="brief",
            title="Source document",
        )
    )
    SqlitePresentationRepository(repository_db_path).create(
        Presentation(
            id=presentation_id,
            session_id=session_id,
            current_file_id=presentation_file.id,
            presentation_type="deck",
            title="Source presentation",
        )
    )

    response = client.post(
        f"/tasks/{task_id}/execute",
        json={
            "stored_file_ids": [stored_file.id],
            "document_ids": [document_id],
            "presentation_ids": [presentation_id],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    artifact_id = payload["result_data"]["artifact_ids"][0]

    assert payload["status"] == "succeeded"
    assert payload["result_data"]["source_mode"] == "stored_source"
    assert payload["result_data"]["source_refs"] == [
        {"kind": "stored_file", "source_id": stored_file.id, "role": "primary_source"},
        {"kind": "document", "source_id": document_id, "role": "primary_source"},
        {"kind": "presentation", "source_id": presentation_id, "role": "primary_source"},
    ]
    assert [item["bullets"][0] for item in payload["result_data"]["outline"][:3]] == [
        "Stored file opportunity",
        "Document source plan",
        "Presentation source risks",
    ]

    sources = SqliteArtifactSourceRepository(repository_db_path).list_by_artifact(artifact_id)
    assert len(sources) == 3
    assert {source.source_file_id for source in sources} == {stored_file.id, None}
    assert {source.source_document_id for source in sources} == {document_id, None}
    assert {source.source_presentation_id for source in sources} == {presentation_id, None}
    _assert_valid_pptx(_download_artifact(artifact_id))
