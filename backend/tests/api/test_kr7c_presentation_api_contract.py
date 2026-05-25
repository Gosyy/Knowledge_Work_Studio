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
from backend.app.services.slides_service import PresentationPlanSnapshotService, build_presentation_plan

client = TestClient(app)


_V1_PATHS = {
    "/api/v1/presentations": {"post"},
    "/api/v1/presentations/{presentation_id}": {"get"},
    "/api/v1/presentations/{presentation_id}/sources": {"post"},
    "/api/v1/presentations/{presentation_id}/plan": {"get", "post"},
    "/api/v1/presentations/{presentation_id}/slides": {"get"},
    "/api/v1/presentations/{presentation_id}/slides/{slide_id}": {"patch"},
    "/api/v1/presentations/{presentation_id}/render": {"post"},
    "/api/v1/presentations/{presentation_id}/export": {"post"},
    "/api/v1/presentations/{presentation_id}/quality": {"get"},
}


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
    app.openapi_schema = None


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
            id="sf_kr7c_v1",
            session_id=session_id,
            task_id="task_kr7c_v1",
            kind="presentation_deck",
            file_type="pptx",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            title="KR-7C deck",
            original_filename="kr7c.pptx",
            storage_backend="local",
            storage_key="presentations/kr7c/sf_kr7c_v1.pptx",
            storage_uri="local://presentations/kr7c/sf_kr7c_v1.pptx",
            checksum_sha256="kr7c",
            size_bytes=2048,
            owner_user_id=owner_user_id,
        )
    )
    SqlitePresentationRepository(repository_db_path).create(
        Presentation(
            id="pres_kr7c",
            session_id=session_id,
            current_file_id="sf_kr7c_v1",
            presentation_type="generated_deck",
            title="KR-7C deck",
        )
    )
    SqlitePresentationVersionRepository(repository_db_path).create(
        PresentationVersion(
            id="presver_kr7c_v1",
            presentation_id="pres_kr7c",
            file_id="sf_kr7c_v1",
            version_number=1,
            created_from_task_id="task_kr7c_v1",
            parent_version_id=None,
            change_summary="Initial KR-7C deck",
        )
    )


def _seed_plan_snapshot(repository_db_path: str) -> None:
    service = PresentationPlanSnapshotService(
        snapshots=SqlitePresentationPlanSnapshotRepository(repository_db_path),
        presentations=SqlitePresentationRepository(repository_db_path),
        presentation_versions=SqlitePresentationVersionRepository(repository_db_path),
    )
    plan = build_presentation_plan(
        "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )
    service.create_snapshot(
        presentation_id="pres_kr7c",
        presentation_version_id="presver_kr7c_v1",
        plan=plan,
        created_from_task_id="task_kr7c_v1",
        change_summary="Initial API-first snapshot",
        snapshot_id="plansnap_kr7c_v1",
    )


def test_kr7c_openapi_exposes_api_v1_presentation_contract_and_legacy_compatibility() -> None:
    schema = app.openapi()
    paths = schema["paths"]

    for path, methods in _V1_PATHS.items():
        assert path in paths
        for method in methods:
            assert method in paths[path]

    assert "/tasks" in paths
    assert "post" in paths["/tasks"]
    assert "/tasks/{task_id}/execute" in paths
    assert "post" in paths["/tasks/{task_id}/execute"]
    assert "/presentations/{presentation_id}" in paths
    assert "get" in paths["/presentations/{presentation_id}"]

    component_schemas = schema["components"]["schemas"]
    assert "PresentationApiCreateRequestSchema" in component_schemas
    assert "PresentationApiPlanSnapshotResponseSchema" in component_schemas
    assert "PresentationApiSlidesResponseSchema" in component_schemas
    assert any(tag["name"] == "presentation-api-v1" for tag in schema["tags"])


def test_kr7c_checker_reports_ready() -> None:
    from scripts.kw_presentation_api_contract_check import build_report

    report = build_report()
    assert report["status"] == "ready"
    assert report["missing_paths"] == []
    assert report["missing_legacy_paths"] == []
    assert report["missing_schemas"] == []


def test_kr7c_gets_presentation_metadata_through_api_v1(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)

    response = client.get("/api/v1/presentations/pres_kr7c")

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_version"] == "presentation_api.v1"
    assert payload["presentation"]["id"] == "pres_kr7c"
    assert payload["presentation"]["current_file"]["id"] == "sf_kr7c_v1"
    assert "storage_key" not in str(payload)
    assert "storage_uri" not in str(payload)


def test_kr7c_gets_public_safe_slides_from_latest_plan_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_plan_snapshot(repository_db_path)

    snapshots = SqlitePresentationPlanSnapshotRepository(repository_db_path)
    latest = snapshots.get_latest_for_presentation("pres_kr7c")
    assert latest is not None
    unsafe_json = dict(latest.snapshot_json)
    unsafe_json["slides"] = list(unsafe_json["slides"])
    unsafe_json["slides"][0] = dict(unsafe_json["slides"][0])
    unsafe_json["slides"][0]["storage_uri"] = "local://secret/path"
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

    response = client.get("/api/v1/presentations/pres_kr7c/slides")

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_version"] == "presentation_api.v1"
    assert payload["presentation_id"] == "pres_kr7c"
    assert payload["snapshot_id"] == "plansnap_kr7c_v1"
    assert payload["schema_version"] == "1"
    assert len(payload["slides"]) == 7
    assert "storage_uri" not in str(payload)
    assert "local://secret" not in str(payload)


def test_kr7c_future_mutation_endpoints_fail_closed() -> None:
    create_response = client.post(
        "/api/v1/presentations",
        json={"objective": "Build an executive deck", "slide_count": 6},
    )
    assert create_response.status_code == 501
    assert "KR-7C API-first Presentation contract endpoint" in create_response.json()["detail"]

    patch_response = client.patch(
        "/api/v1/presentations/pres_kr7c/slides/slide_001",
        json={"title": "New title", "content": {"bullets": ["A"]}},
    )
    assert patch_response.status_code == 501
