from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.domain import Presentation, PresentationPlanSnapshot, PresentationVersion, StoredFile
from backend.app.main import app
from backend.app.repositories.sqlite import (
    SqlitePresentationPlanSnapshotRepository,
    SqlitePresentationRepository,
    SqlitePresentationVersionRepository,
    SqliteStoredFileRepository,
)
from backend.app.services.slides_service import PresentationPlanSnapshotService, build_presentation_plan, serialize_presentation_plan

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


def _register_presentation(*, repository_db_path: str, session_id: str, owner_user_id: str = "user_local_default") -> None:
    SqliteStoredFileRepository(repository_db_path).create(
        StoredFile(
            id="sf_o3_v2",
            session_id=session_id,
            task_id="task_o3_v2",
            kind="presentation_deck",
            file_type="pptx",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            title="O3 deck",
            original_filename="o3.pptx",
            storage_backend="local",
            storage_key="presentations/o3/sf_o3_v2.pptx",
            storage_uri="local://presentations/o3/sf_o3_v2.pptx",
            checksum_sha256="o3",
            size_bytes=2048,
            owner_user_id=owner_user_id,
        )
    )
    presentations = SqlitePresentationRepository(repository_db_path)
    versions = SqlitePresentationVersionRepository(repository_db_path)
    presentations.create(
        Presentation(
            id="pres_o3",
            session_id=session_id,
            current_file_id="sf_o3_v2",
            presentation_type="generated_deck",
            title="O3 deck",
        )
    )
    versions.create(
        PresentationVersion(
            id="presver_o3_v1",
            presentation_id="pres_o3",
            file_id="sf_o3_v1",
            version_number=1,
            created_from_task_id="task_o3_v1",
            parent_version_id=None,
            change_summary="Initial",
        )
    )
    versions.create(
        PresentationVersion(
            id="presver_o3_v2",
            presentation_id="pres_o3",
            file_id="sf_o3_v2",
            version_number=2,
            created_from_task_id="task_o3_v2",
            parent_version_id="presver_o3_v1",
            change_summary="Revision",
        )
    )


def _seed_snapshots(repository_db_path: str) -> None:
    presentations = SqlitePresentationRepository(repository_db_path)
    versions = SqlitePresentationVersionRepository(repository_db_path)
    snapshots = SqlitePresentationPlanSnapshotRepository(repository_db_path)
    service = PresentationPlanSnapshotService(
        snapshots=snapshots,
        presentations=presentations,
        presentation_versions=versions,
    )

    v1 = build_presentation_plan(
        "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )
    slides = list(v1.slides)
    slides[2] = replace(
        slides[2],
        title="Revised analysis title",
        bullets=tuple(list(slides[2].bullets) + ["New O3 evidence bullet"]),
        speaker_notes="Updated O3 notes.",
    )
    v2 = replace(v1, slides=tuple(slides))

    service.create_snapshot(
        presentation_id="pres_o3",
        presentation_version_id="presver_o3_v1",
        plan=v1,
        created_from_task_id="task_o3_v1",
        change_summary="Initial snapshot",
        snapshot_id="plansnap_o3_v1",
    )
    service.create_snapshot(
        presentation_id="pres_o3",
        presentation_version_id="presver_o3_v2",
        plan=v2,
        created_from_task_id="task_o3_v2",
        change_summary="Revision snapshot",
        snapshot_id="plansnap_o3_v2",
    )


def test_o3_gets_current_plan_snapshot_with_safe_public_payload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_snapshots(repository_db_path)

    # Force an unsafe key into stored snapshot JSON to prove public response sanitization.
    snapshots = SqlitePresentationPlanSnapshotRepository(repository_db_path)
    latest = snapshots.get_latest_for_presentation("pres_o3")
    assert latest is not None
    unsafe_json = dict(latest.snapshot_json)
    unsafe_json["storage_uri"] = "local://secret/internal/path"
    unsafe_json["slides"] = list(unsafe_json["slides"])
    unsafe_json["slides"][0] = dict(unsafe_json["slides"][0])
    unsafe_json["slides"][0]["storage_key"] = "private/key"
    snapshots.create(
        PresentationPlanSnapshot(
            id=latest.id,
            presentation_id=latest.presentation_id,
            presentation_version_id=latest.presentation_version_id,
            snapshot_json=unsafe_json,
            created_from_task_id=latest.created_from_task_id,
            change_summary=latest.change_summary,
            created_at=latest.created_at,
        )
    )

    response = client.get("/presentations/pres_o3/plan")

    assert response.status_code == 200
    payload = response.json()
    assert payload["snapshot_id"] == "plansnap_o3_v2"
    assert payload["presentation_version_id"] == "presver_o3_v2"
    assert payload["plan"]["deck_title"]
    assert "storage_uri" not in str(payload)
    assert "storage_key" not in str(payload)
    assert "local://secret" not in str(payload)


def test_o3_gets_version_specific_plan_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_snapshots(repository_db_path)

    response = client.get("/presentations/pres_o3/versions/presver_o3_v1/plan")

    assert response.status_code == 200
    payload = response.json()
    assert payload["snapshot_id"] == "plansnap_o3_v1"
    assert payload["presentation_version_id"] == "presver_o3_v1"
    assert payload["plan"]["slides"][2]["title"] != "Revised analysis title"


def test_o3_gets_revision_plan_diff(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_snapshots(repository_db_path)

    response = client.get("/presentations/pres_o3/revisions/presver_o3_v2/diff")

    assert response.status_code == 200
    payload = response.json()
    assert payload["presentation_id"] == "pres_o3"
    assert payload["base_version_id"] == "presver_o3_v1"
    assert payload["compared_version_id"] == "presver_o3_v2"
    assert payload["base_snapshot_id"] == "plansnap_o3_v1"
    assert payload["compared_snapshot_id"] == "plansnap_o3_v2"
    assert payload["changed_slide_count"] == 1
    assert payload["slide_deltas"][0]["slide_id"] == "slide_003"
    assert payload["slide_deltas"][0]["change_type"] == "modified"
    assert payload["slide_deltas"][0]["title_after"] == "Revised analysis title"
    assert payload["slide_deltas"][0]["bullets_added"] == ["New O3 evidence bullet"]
    assert payload["slide_deltas"][0]["speaker_notes_changed"] is True


def test_o3_current_plan_missing_returns_404(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)

    response = client.get("/presentations/pres_o3/plan")

    assert response.status_code == 404
    assert "no editable plan snapshot" in response.json()["detail"]


def test_o3_version_plan_is_owner_scoped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session(headers={"X-User-Id": "alice"})
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id, owner_user_id="alice")
    _seed_snapshots(repository_db_path)

    response = client.get(
        "/presentations/pres_o3/versions/presver_o3_v1/plan",
        headers={"X-User-Id": "bob"},
    )

    assert response.status_code == 404


def test_o3_revision_diff_missing_comparable_snapshot_returns_404(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    snapshots = SqlitePresentationPlanSnapshotRepository(repository_db_path)
    snapshots.create(
        PresentationPlanSnapshot(
            id="plansnap_o3_v2_only",
            presentation_id="pres_o3",
            presentation_version_id="presver_o3_v2",
            snapshot_json=serialize_presentation_plan(
                build_presentation_plan("Opening. Context. Analysis. Close.", min_slides=5, max_slides=5)
            ),
            created_from_task_id="task_o3_v2",
            change_summary="Only compared snapshot",
        )
    )

    response = client.get("/presentations/pres_o3/revisions/presver_o3_v2/diff")

    assert response.status_code == 404
    assert "Comparable presentation plan snapshots" in response.json()["detail"]
