from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app
from backend.app.repositories.sqlite import SqliteDerivedContentRepository, SqliteStoredFileRepository

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


def _create_session_upload_and_task(content: bytes) -> tuple[str, str, str]:
    session_response = client.post("/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    upload_response = client.post(
        "/uploads",
        data={"session_id": session_id},
        files={"file": ("source.txt", content, "text/plain")},
    )
    assert upload_response.status_code == 201
    upload_id = upload_response.json()["id"]

    task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "pdf_summary"},
    )
    assert task_response.status_code == 201
    return session_id, upload_id, task_response.json()["id"]


def test_j3_repeated_generation_reuses_cached_derived_content_instead_of_rereading_storage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    original_text = b"Original first. Original second. Original third."
    session_id, upload_id, first_task_id = _create_session_upload_and_task(original_text)

    first_response = client.post(
        f"/tasks/{first_task_id}/execute",
        json={"uploaded_file_ids": [upload_id]},
    )
    assert first_response.status_code == 200
    assert first_response.json()["result_data"]["output_text"] == "Original first. Original second."

    derived_repository = SqliteDerivedContentRepository(repository_db_path)
    derived_rows = derived_repository.list_by_file(upload_id)
    assert len(derived_rows) == 1
    assert derived_rows[0].content_kind == "extracted_text"
    assert derived_rows[0].text_content == original_text.decode("utf-8")

    stored_file = SqliteStoredFileRepository(repository_db_path).get(upload_id)
    assert stored_file is not None

    # Mutate the binary storage layer after extraction. A second generation from
    # the same source must reuse derived_contents, proving repeated parsing/read
    # work has been reduced by the metadata model.
    app.state.app_container.task_source_service.storage.save_bytes(
        storage_key=stored_file.storage_key,
        content=b"Changed first. Changed second. Changed third.",
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

    assert second_payload["result_data"]["output_text"] == "Original first. Original second."
    assert "Changed first" not in second_payload["result_data"]["output_text"]
    assert len(derived_repository.list_by_file(upload_id)) == 1
