from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.domain import StoredFile
from backend.app.main import app
from backend.app.repositories import SqliteLLMRunRepository
from backend.app.repositories.sqlite import SqliteStoredFileRepository

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


def _configure_sqlite_fake_llm_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> str:
    repository_db_path = str(tmp_path / "repositories.sqlite3")
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("REPOSITORY_DB_PATH", repository_db_path)
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.setenv("FAKE_LLM_RESPONSE", "semantic-provider-output")
    get_settings.cache_clear()
    _reset_app_state()
    return repository_db_path


def _create_session_and_task(task_type: str = "pdf_summary") -> tuple[str, str]:
    session_response = client.post("/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": task_type},
    )
    assert task_response.status_code == 201
    return session_id, task_response.json()["id"]


def _assert_single_llm_run(repository_db_path: str, *, task_id: str, workflow: str) -> None:
    runs = SqliteLLMRunRepository(repository_db_path).list_by_task(task_id)
    assert len(runs) == 1
    assert runs[0].task_id == task_id
    assert runs[0].workflow == workflow
    assert runs[0].provider == "fake"
    assert runs[0].status == "succeeded"
    assert runs[0].response_text == "semantic-provider-output"


def test_i3_prompt_only_semantic_task_uses_provider_and_records_llm_run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_fake_llm_env(monkeypatch, tmp_path)
    _, task_id = _create_session_and_task()

    response = client.post(
        f"/tasks/{task_id}/semantic",
        json={
            "workflow": "summarization",
            "content": "Alpha. Beta. Gamma.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["result_data"]["semantic_workflow"] == "summarization"
    assert payload["result_data"]["output_text"] == "semantic-provider-output"
    assert payload["result_data"]["source_mode"] == "prompt_only"
    assert payload["result_data"]["source_refs"] == []
    _assert_single_llm_run(repository_db_path, task_id=task_id, workflow="summarization")


def test_i3_uploaded_source_semantic_task_uses_provider_and_records_source_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_fake_llm_env(monkeypatch, tmp_path)
    session_id, task_id = _create_session_and_task()

    upload_response = client.post(
        "/uploads",
        data={"session_id": session_id},
        files={"file": ("notes.txt", b"Draft text from upload.", "text/plain")},
    )
    assert upload_response.status_code == 201
    upload_id = upload_response.json()["id"]

    response = client.post(
        f"/tasks/{task_id}/semantic",
        json={
            "workflow": "rewriting",
            "instruction": "Make it formal.",
            "uploaded_file_ids": [upload_id],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["result_data"]["semantic_workflow"] == "rewriting"
    assert payload["result_data"]["source_mode"] == "uploaded_source"
    assert payload["result_data"]["source_refs"] == [
        {"kind": "uploaded_file", "source_id": upload_id, "role": "primary_source"}
    ]
    _assert_single_llm_run(repository_db_path, task_id=task_id, workflow="rewriting")


def test_i3_stored_source_semantic_task_uses_provider_and_records_source_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_fake_llm_env(monkeypatch, tmp_path)
    session_id, task_id = _create_session_and_task()

    assert hasattr(app.state, "app_container")
    storage = app.state.app_container.task_source_service.storage

    stored_file_id = "sf_i3_source"
    storage_key = f"stored/{session_id}/{stored_file_id}/source.txt"
    storage_uri = storage.save_bytes(
        storage_key=storage_key,
        content=b"Stored source for outline.",
    )
    SqliteStoredFileRepository(repository_db_path).create(
        StoredFile(
            id=stored_file_id,
            session_id=session_id,
            task_id=None,
            kind="uploaded_source",
            file_type="txt",
            mime_type="text/plain",
            title="Stored source",
            original_filename="source.txt",
            storage_backend=storage.backend_name,
            storage_key=storage_key,
            storage_uri=storage_uri,
            checksum_sha256=None,
            size_bytes=len(b"Stored source for outline."),
        )
    )

    response = client.post(
        f"/tasks/{task_id}/semantic",
        json={
            "workflow": "outline_generation",
            "stored_file_ids": [stored_file_id],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["result_data"]["semantic_workflow"] == "outline_generation"
    assert payload["result_data"]["source_mode"] == "stored_source"
    assert payload["result_data"]["source_refs"] == [
        {"kind": "stored_file", "source_id": stored_file_id, "role": "primary_source"}
    ]
    _assert_single_llm_run(repository_db_path, task_id=task_id, workflow="outline_generation")
