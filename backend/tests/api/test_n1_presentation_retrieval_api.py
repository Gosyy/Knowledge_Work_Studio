from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.domain import Presentation, PresentationVersion, StoredFile
from backend.app.main import app
from backend.app.repositories.sqlite import (
    SqlitePresentationRepository,
    SqlitePresentationVersionRepository,
    SqliteStoredFileRepository,
)

client = TestClient(app)


def _reset_app_state() -> None:
    for attribute in (
        "app_container",
        "g1_execution_coordinator",
        "official_execution_coordinator",
        "task_queue_service",
        "llm_provider",
        "llm_text_service",
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


def _create_session(headers: dict[str, str] | None = None) -> str:
    response = client.post("/sessions", json={}, headers=headers or {})
    assert response.status_code == 201
    return response.json()["id"]


def _register_presentation(
    *,
    repository_db_path: str,
    session_id: str,
    presentation_id: str = "pres_n1",
    file_id: str = "sf_n1",
    with_version: bool = True,
) -> None:
    stored_files = SqliteStoredFileRepository(repository_db_path)
    presentations = SqlitePresentationRepository(repository_db_path)
    versions = SqlitePresentationVersionRepository(repository_db_path)

    stored_files.create(
        StoredFile(
            id=file_id,
            session_id=session_id,
            task_id="task_n1",
            kind="presentation_deck",
            file_type="pptx",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            title="N1 deck file",
            original_filename="n1_deck.pptx",
            storage_backend="local",
            storage_key=f"presentations/{session_id}/{file_id}.pptx",
            storage_uri=f"local://presentations/{session_id}/{file_id}.pptx",
            checksum_sha256="abc123",
            size_bytes=2048,
            owner_user_id="user_local_default",
        )
    )
    presentations.create(
        Presentation(
            id=presentation_id,
            session_id=session_id,
            current_file_id=file_id,
            presentation_type="generated_deck",
            title="N1 deck",
        )
    )
    if with_version:
        versions.create(
            PresentationVersion(
                id="presver_n1",
                presentation_id=presentation_id,
                file_id=file_id,
                version_number=1,
                created_from_task_id="task_n1",
                parent_version_id=None,
                change_summary="Initial deck",
            )
        )


def test_n1_lists_session_presentations_with_safe_current_file_ref(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)

    response = client.get(f"/sessions/{session_id}/presentations")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1

    item = payload[0]
    assert item["id"] == "pres_n1"
    assert item["session_id"] == session_id
    assert item["current_file_id"] == "sf_n1"
    assert item["presentation_type"] == "generated_deck"
    assert item["title"] == "N1 deck"
    assert item["current_file"]["id"] == "sf_n1"
    assert item["current_file"]["file_type"] == "pptx"
    assert item["current_file"]["checksum_sha256"] == "abc123"
    assert item["latest_version"]["version_number"] == 1

    assert "storage_key" not in item["current_file"]
    assert "storage_uri" not in item["current_file"]


def test_n1_gets_presentation_metadata_by_id(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)

    response = client.get("/presentations/pres_n1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "pres_n1"
    assert payload["current_file"]["original_filename"] == "n1_deck.pptx"
    assert payload["latest_version"]["id"] == "presver_n1"


def test_n1_does_not_fake_version_when_none_exists(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(
        repository_db_path=repository_db_path,
        session_id=session_id,
        presentation_id="pres_no_version",
        file_id="sf_no_version",
        with_version=False,
    )

    response = client.get("/presentations/pres_no_version")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "pres_no_version"
    assert payload["latest_version"] is None


def test_n1_missing_presentation_returns_404(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_sqlite_test_env(monkeypatch, tmp_path)

    response = client.get("/presentations/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Presentation not found"


def test_n1_presentation_access_is_session_owner_scoped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session(headers={"X-User-Id": "alice"})
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)

    own_response = client.get(
        f"/sessions/{session_id}/presentations",
        headers={"X-User-Id": "alice"},
    )
    assert own_response.status_code == 200
    assert len(own_response.json()) == 1

    foreign_list_response = client.get(
        f"/sessions/{session_id}/presentations",
        headers={"X-User-Id": "bob"},
    )
    assert foreign_list_response.status_code == 404

    foreign_get_response = client.get(
        "/presentations/pres_n1",
        headers={"X-User-Id": "bob"},
    )
    assert foreign_get_response.status_code == 404
