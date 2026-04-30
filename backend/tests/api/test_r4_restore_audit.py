from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.tests.api.test_p4_revision_restore_api import _seed_v1_file
from backend.tests.api.test_o3_plan_snapshot_inspection_api import (
    _configure_sqlite_test_env,
    _create_session,
    _register_presentation,
    _seed_snapshots,
)

client = TestClient(app)


def _seed_restore_fixture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    owner_user_id: str = "user_local_default",
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    headers = {"X-User-Id": owner_user_id} if owner_user_id != "user_local_default" else None
    session_id = _create_session(headers=headers)
    _register_presentation(
        repository_db_path=repository_db_path,
        session_id=session_id,
        owner_user_id=owner_user_id,
    )
    _seed_v1_file(repository_db_path, session_id=session_id, owner_user_id=owner_user_id)
    _seed_snapshots(repository_db_path)


def test_r4_restore_returns_audit_metadata_and_persists_reason(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _seed_restore_fixture(monkeypatch, tmp_path, owner_user_id="alice")

    response = client.post(
        "/presentations/pres_o3/versions/presver_o3_v1/restore",
        headers={"X-User-Id": "alice"},
        json={
            "confirmation": "RESTORE",
            "confirmation_target_version_id": "presver_o3_v1",
            "restore_reason": "Operator requested rollback after review.",
            "task_id": "task_r4_restore",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["restored_by_user_id"] == "alice"
    assert payload["restore_reason"] == "Operator requested rollback after review."
    assert "alice" in payload["audit_summary"]
    assert "presver_o3_v1" in payload["audit_summary"]
    assert "presver_o3_v2" in payload["audit_summary"]
    assert "Operator requested rollback after review." in payload["change_summary"]

    versions_response = client.get("/presentations/pres_o3/versions", headers={"X-User-Id": "alice"})
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert versions[-1]["id"] == payload["restored_version_id"]
    assert versions[-1]["change_summary"] == payload["change_summary"]


def test_r4_restore_rejects_mismatched_target_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _seed_restore_fixture(monkeypatch, tmp_path)

    response = client.post(
        "/presentations/pres_o3/versions/presver_o3_v1/restore",
        json={
            "confirmation": "RESTORE",
            "confirmation_target_version_id": "presver_o3_v2",
            "restore_reason": "Operator requested rollback after review.",
        },
    )

    assert response.status_code == 400
    assert "target version id" in response.json()["detail"]


def test_r4_restore_rejects_too_short_reason(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _seed_restore_fixture(monkeypatch, tmp_path)

    response = client.post(
        "/presentations/pres_o3/versions/presver_o3_v1/restore",
        json={
            "confirmation": "RESTORE",
            "confirmation_target_version_id": "presver_o3_v1",
            "restore_reason": "short",
        },
    )

    assert response.status_code == 422
