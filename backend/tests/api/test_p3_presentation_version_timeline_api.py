from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.tests.api.test_o3_plan_snapshot_inspection_api import (
    _configure_sqlite_test_env,
    _create_session,
    _register_presentation,
)

client = TestClient(app)


def test_p3_lists_presentation_versions_in_lineage_order(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)

    response = client.get("/presentations/pres_o3/versions")

    assert response.status_code == 200
    versions = response.json()
    assert [version["id"] for version in versions] == ["presver_o3_v1", "presver_o3_v2"]
    assert [version["version_number"] for version in versions] == [1, 2]
    assert versions[0]["parent_version_id"] is None
    assert versions[1]["parent_version_id"] == "presver_o3_v1"
    assert versions[1]["change_summary"] == "Revision"
    assert "storage_key" not in str(versions)
    assert "storage_uri" not in str(versions)


def test_p3_version_list_is_owner_scoped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session(headers={"X-User-Id": "alice"})
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id, owner_user_id="alice")

    own_response = client.get("/presentations/pres_o3/versions", headers={"X-User-Id": "alice"})
    other_response = client.get("/presentations/pres_o3/versions", headers={"X-User-Id": "bob"})

    assert own_response.status_code == 200
    assert len(own_response.json()) == 2
    assert other_response.status_code == 404


def test_p3_version_list_missing_presentation_returns_404(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_sqlite_test_env(monkeypatch, tmp_path)

    response = client.get("/presentations/pres_missing/versions")

    assert response.status_code == 404
    assert response.json()["detail"] == "Presentation not found"
