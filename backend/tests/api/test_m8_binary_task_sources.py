from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.domain import Presentation, StoredFile
from backend.app.main import app
from backend.app.repositories.sqlite import (
    SqliteDerivedContentRepository,
    SqlitePresentationRepository,
    SqliteStoredFileRepository,
)
from backend.app.services.docx_service.builder import build_docx_package
from backend.app.services.slides_service.generator import generate_pptx_from_outline
from backend.app.services.slides_service.outline import SlideOutlineItem

client = TestClient(app)


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
PDF_MIME = "application/pdf"


def _reset_app_state() -> None:
    for attribute in (
        "app_container",
        "g1_execution_coordinator",
        "official_execution_coordinator",
        "llm_provider",
        "llm_text_service",
        "task_queue_service",
    ):
        if hasattr(app.state, attribute):
            delattr(app.state, attribute)


def _configure_sqlite_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> str:
    repository_db_path = str(tmp_path / "repositories.sqlite3")
    monkeypatch.setenv("APP_ENV", "test")
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


def _create_session_and_task() -> tuple[str, str]:
    session_response = client.post("/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "pdf_summary"},
    )
    assert task_response.status_code == 201
    return session_id, task_response.json()["id"]


def test_m8_uploaded_docx_source_feeds_execution_and_reuses_cached_extraction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id, first_task_id = _create_session_and_task()

    original_docx = build_docx_package("Alpha first. Beta second. Gamma third.")
    upload_response = client.post(
        "/uploads",
        data={"session_id": session_id},
        files={"file": ("source.docx", original_docx, DOCX_MIME)},
    )
    assert upload_response.status_code == 201
    upload_id = upload_response.json()["id"]

    first_response = client.post(
        f"/tasks/{first_task_id}/execute",
        json={"uploaded_file_ids": [upload_id]},
    )
    assert first_response.status_code == 200
    first_payload = first_response.json()
    assert first_payload["status"] == "succeeded"
    assert first_payload["result_data"]["source_mode"] == "uploaded_source"
    assert first_payload["result_data"]["output_text"] == "Alpha first. Beta second."

    derived_repository = SqliteDerivedContentRepository(repository_db_path)
    derived_rows = derived_repository.list_by_file(upload_id)
    assert len(derived_rows) == 1
    assert derived_rows[0].content_kind == "extracted_text"
    assert derived_rows[0].text_content == "Alpha first. Beta second. Gamma third."

    stored_file = SqliteStoredFileRepository(repository_db_path).get(upload_id)
    assert stored_file is not None
    changed_docx = build_docx_package("Changed first. Changed second. Changed third.")
    app.state.app_container.task_source_service.storage.save_bytes(
        storage_key=stored_file.storage_key,
        content=changed_docx,
    )

    second_task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "pdf_summary"},
    )
    assert second_task_response.status_code == 201
    second_task_id = second_task_response.json()["id"]

    second_response = client.post(
        f"/tasks/{second_task_id}/execute",
        json={"uploaded_file_ids": [upload_id]},
    )
    assert second_response.status_code == 200
    second_payload = second_response.json()
    assert second_payload["result_data"]["output_text"] == "Alpha first. Beta second."
    assert len(derived_repository.list_by_file(upload_id)) == 1


def test_m8_pptx_stored_source_feeds_execution_and_caches_outline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id, task_id = _create_session_and_task()

    storage = app.state.app_container.task_source_service.storage
    stored_files = SqliteStoredFileRepository(repository_db_path)
    presentations = SqlitePresentationRepository(repository_db_path)

    pptx_bytes = generate_pptx_from_outline(
        (
            SlideOutlineItem(title="Quarterly roadmap", bullets=("Launch API", "Measure adoption")),
            SlideOutlineItem(title="Risks", bullets=("Budget pressure", "Staffing")),
        )
    )
    stored_file_id = "sf_m8_pptx"
    storage_key = f"stored/{session_id}/{stored_file_id}/slides.pptx"
    storage_uri = storage.save_bytes(storage_key=storage_key, content=pptx_bytes, content_type=PPTX_MIME)
    stored_files.create(
        StoredFile(
            id=stored_file_id,
            session_id=session_id,
            task_id=None,
            kind="uploaded_source",
            file_type="pptx",
            mime_type=PPTX_MIME,
            title="Slides source",
            original_filename="slides.pptx",
            storage_backend=storage.backend_name,
            storage_key=storage_key,
            storage_uri=storage_uri,
            checksum_sha256=None,
            size_bytes=len(pptx_bytes),
        )
    )
    presentation_id = "pres_m8"
    presentations.create(
        Presentation(
            id=presentation_id,
            session_id=session_id,
            current_file_id=stored_file_id,
            presentation_type="status_update",
            title="Stored presentation",
        )
    )

    response = client.post(
        f"/tasks/{task_id}/execute",
        json={"presentation_ids": [presentation_id]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["result_data"]["source_mode"] == "stored_source"
    assert "Quarterly roadmap" in payload["result_data"]["output_text"]

    derived_rows = SqliteDerivedContentRepository(repository_db_path).list_by_file(stored_file_id)
    assert len(derived_rows) == 1
    assert derived_rows[0].content_kind == "extracted_text"
    assert derived_rows[0].outline_json == {
        "slides": [
            {"title": "Quarterly roadmap", "bullets": ["Launch API", "Measure adoption"]},
            {"title": "Risks", "bullets": ["Budget pressure", "Staffing"]},
        ]
    }


def test_m8_pdf_binary_source_fails_honestly(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id, task_id = _create_session_and_task()

    storage = app.state.app_container.task_source_service.storage
    stored_files = SqliteStoredFileRepository(repository_db_path)

    stored_file_id = "sf_m8_pdf"
    storage_key = f"stored/{session_id}/{stored_file_id}/source.pdf"
    storage_uri = storage.save_bytes(storage_key=storage_key, content=b"%PDF-1.4\n%fake\n", content_type=PDF_MIME)
    stored_files.create(
        StoredFile(
            id=stored_file_id,
            session_id=session_id,
            task_id=None,
            kind="uploaded_source",
            file_type="pdf",
            mime_type=PDF_MIME,
            title="PDF source",
            original_filename="source.pdf",
            storage_backend=storage.backend_name,
            storage_key=storage_key,
            storage_uri=storage_uri,
            checksum_sha256=None,
            size_bytes=len(b"%PDF-1.4\n%fake\n"),
        )
    )

    response = client.post(
        f"/tasks/{task_id}/execute",
        json={"stored_file_ids": [stored_file_id]},
    )
    assert response.status_code == 409
    assert "does not fake PDF extraction" in response.json()["detail"]
