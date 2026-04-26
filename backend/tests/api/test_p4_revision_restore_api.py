from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.domain import StoredFile
from backend.app.main import app
from backend.app.repositories.sqlite import SqliteStoredFileRepository
from backend.tests.api.test_o3_plan_snapshot_inspection_api import (
    _configure_sqlite_test_env,
    _create_session,
    _register_presentation,
    _seed_snapshots,
)

client = TestClient(app)


def _seed_v1_file(repository_db_path: str, *, session_id: str, owner_user_id: str = "user_local_default") -> None:
    SqliteStoredFileRepository(repository_db_path).create(
        StoredFile(
            id="sf_o3_v1",
            session_id=session_id,
            task_id="task_o3_v1",
            kind="presentation_deck",
            file_type="pptx",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            title="O3 deck v1",
            original_filename="o3_v1.pptx",
            storage_backend="local",
            storage_key="presentations/o3/sf_o3_v1.pptx",
            storage_uri="local://presentations/o3/sf_o3_v1.pptx",
            checksum_sha256="o3-v1",
            size_bytes=1024,
            owner_user_id=owner_user_id,
        )
    )


def test_p4_restores_previous_version_by_creating_new_lineage_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_v1_file(repository_db_path, session_id=session_id)
    _seed_snapshots(repository_db_path)

    response = client.post(
        "/presentations/pres_o3/versions/presver_o3_v1/restore",
        json={
            "confirmation": "RESTORE",
            "change_summary": "Restore initial deck",
            "task_id": "task_restore_v1",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["presentation_id"] == "pres_o3"
    assert payload["target_version_id"] == "presver_o3_v1"
    assert payload["target_version_number"] == 1
    assert payload["restored_version_number"] == 3
    assert payload["parent_version_id"] == "presver_o3_v2"
    assert payload["current_file_id"] == "sf_o3_v1"
    assert payload["previous_file_id"] == "sf_o3_v2"
    assert payload["change_summary"] == "Restore initial deck"

    presentation_response = client.get("/presentations/pres_o3")
    assert presentation_response.status_code == 200
    presentation = presentation_response.json()
    assert presentation["current_file_id"] == "sf_o3_v1"
    assert presentation["current_file"]["id"] == "sf_o3_v1"
    assert presentation["latest_version"]["id"] == payload["restored_version_id"]
    assert presentation["latest_version"]["version_number"] == 3

    restored_plan_response = client.get(
        f"/presentations/pres_o3/versions/{payload['restored_version_id']}/plan"
    )
    assert restored_plan_response.status_code == 200
    restored_plan = restored_plan_response.json()
    assert restored_plan["presentation_version_id"] == payload["restored_version_id"]
    assert restored_plan["plan"]["slides"][2]["title"] != "Revised analysis title"

    restored_diff_response = client.get(
        f"/presentations/pres_o3/revisions/{payload['restored_version_id']}/diff"
    )
    assert restored_diff_response.status_code == 200
    restored_diff = restored_diff_response.json()
    assert restored_diff["base_version_id"] == "presver_o3_v2"
    assert restored_diff["compared_version_id"] == payload["restored_version_id"]
    assert restored_diff["changed_slide_count"] == 1
    assert restored_diff["slide_deltas"][0]["bullets_removed"] == ["New O3 evidence bullet"]


def test_p4_restore_requires_deliberate_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_v1_file(repository_db_path, session_id=session_id)
    _seed_snapshots(repository_db_path)

    response = client.post(
        "/presentations/pres_o3/versions/presver_o3_v1/restore",
        json={"confirmation": "restore"},
    )

    assert response.status_code == 400
    assert "RESTORE" in response.json()["detail"]


def test_p4_restore_is_owner_scoped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session(headers={"X-User-Id": "alice"})
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id, owner_user_id="alice")
    _seed_v1_file(repository_db_path, session_id=session_id, owner_user_id="alice")
    _seed_snapshots(repository_db_path)

    response = client.post(
        "/presentations/pres_o3/versions/presver_o3_v1/restore",
        headers={"X-User-Id": "bob"},
        json={"confirmation": "RESTORE"},
    )

    assert response.status_code == 404


def test_p4_restore_requires_target_plan_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_v1_file(repository_db_path, session_id=session_id)

    response = client.post(
        "/presentations/pres_o3/versions/presver_o3_v1/restore",
        json={"confirmation": "RESTORE"},
    )

    assert response.status_code == 409
    assert "no editable plan snapshot" in response.json()["detail"]


def test_p4_restore_rejects_already_current_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_v1_file(repository_db_path, session_id=session_id)
    _seed_snapshots(repository_db_path)

    response = client.post(
        "/presentations/pres_o3/versions/presver_o3_v2/restore",
        json={"confirmation": "RESTORE"},
    )

    assert response.status_code == 400
    assert "already current" in response.json()["detail"]
