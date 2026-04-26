from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.domain import Artifact, Task, TaskStatus, TaskType
from backend.app.main import app
from backend.app.repositories.sqlite import SqliteArtifactRepository, SqliteTaskRepository
from backend.tests.api.test_n1_presentation_retrieval_api import (
    _configure_sqlite_test_env,
    _create_session,
)

client = TestClient(app)


def _seed_artifact(
    *,
    repository_db_path: str,
    storage_root: Path,
    session_id: str,
    owner_user_id: str = "user_local_default",
    artifact_id: str = "art_p5",
    filename: str = "..\\exports/Презентация\r\nv1.pptx",
    content: bytes = b"deck-bytes",
    write_content: bool = True,
) -> str:
    task_id = f"task_{artifact_id}"
    SqliteTaskRepository(repository_db_path).create(
        Task(
            id=task_id,
            session_id=session_id,
            task_type=TaskType.SLIDES_GENERATE,
            status=TaskStatus.SUCCEEDED,
            owner_user_id=owner_user_id,
        )
    )

    storage_key = f"artifacts/{session_id}/{task_id}/{artifact_id}/deck.pptx"
    if write_content:
        target = storage_root / storage_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    SqliteArtifactRepository(repository_db_path).create(
        Artifact(
            id=artifact_id,
            session_id=session_id,
            task_id=task_id,
            filename=filename,
            content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            owner_user_id=owner_user_id,
            storage_backend="local",
            storage_key=storage_key,
            storage_uri=f"local://{storage_key}",
            size_bytes=len(content),
        )
    )
    return artifact_id


def test_p5_artifact_metadata_is_safe_and_contains_download_url(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    artifact_id = _seed_artifact(
        repository_db_path=repository_db_path,
        storage_root=tmp_path,
        session_id=session_id,
    )

    response = client.get(f"/artifacts/{artifact_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == artifact_id
    assert payload["download_url"] == f"/artifacts/{artifact_id}/download"
    assert payload["content_type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    assert payload["size_bytes"] == len(b"deck-bytes")
    assert "storage_key" not in payload
    assert "storage_uri" not in payload
    assert "local://" not in str(payload)


def test_p5_session_artifact_list_uses_safe_public_schema(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    artifact_id = _seed_artifact(
        repository_db_path=repository_db_path,
        storage_root=tmp_path,
        session_id=session_id,
    )

    response = client.get(f"/sessions/{session_id}/artifacts")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == artifact_id
    assert payload[0]["download_url"] == f"/artifacts/{artifact_id}/download"
    assert "storage_key" not in payload[0]
    assert "storage_uri" not in payload[0]


def test_p5_download_uses_safe_headers_without_leaking_storage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    artifact_id = _seed_artifact(
        repository_db_path=repository_db_path,
        storage_root=tmp_path,
        session_id=session_id,
    )

    response = client.get(f"/artifacts/{artifact_id}/download")

    assert response.status_code == 200
    assert response.content == b"deck-bytes"
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["content-length"] == str(len(b"deck-bytes"))

    disposition = response.headers["content-disposition"]
    assert disposition.startswith("attachment;")
    assert "filename=" in disposition
    assert "filename*=UTF-8''" in disposition
    assert "%D0%9F" in disposition
    assert "local://" not in disposition
    assert ".." not in disposition
    assert "/" not in disposition
    assert "\\" not in disposition
    assert "\r" not in disposition
    assert "\n" not in disposition


def test_p5_download_is_owner_scoped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session(headers={"X-User-Id": "alice"})
    artifact_id = _seed_artifact(
        repository_db_path=repository_db_path,
        storage_root=tmp_path,
        session_id=session_id,
        owner_user_id="alice",
    )

    own_response = client.get(f"/artifacts/{artifact_id}/download", headers={"X-User-Id": "alice"})
    other_response = client.get(f"/artifacts/{artifact_id}/download", headers={"X-User-Id": "bob"})

    assert own_response.status_code == 200
    assert other_response.status_code == 404


def test_p5_missing_artifact_file_returns_404_without_storage_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    artifact_id = _seed_artifact(
        repository_db_path=repository_db_path,
        storage_root=tmp_path,
        session_id=session_id,
        write_content=False,
    )

    response = client.get(f"/artifacts/{artifact_id}/download")

    assert response.status_code == 404
    assert response.json()["detail"] == "Artifact file not found"
    assert "local://" not in str(response.json())
    assert "artifacts/" not in str(response.json())
