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
from backend.app.services.slides_service import (
    PRESENTATION_IR_SCHEMA_VERSION,
    PRESENTATION_IR_SOURCE_ATTACHMENT_CONTRACT_VERSION,
    PresentationPlanSnapshotService,
    build_presentation_ir_from_legacy_plan,
    build_presentation_plan,
)

client = TestClient(app)


_V1_PATHS = {
    "/api/v1/presentations": {"post"},
    "/api/v1/presentations/{presentation_id}": {"get"},
    "/api/v1/presentations/{presentation_id}/sources": {"get", "post"},
    "/api/v1/presentations/{presentation_id}/plan": {"get", "post"},
    "/api/v1/presentations/{presentation_id}/ir": {"get"},
    "/api/v1/presentations/{presentation_id}/ir/versions": {"get"},
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


def _seed_native_presentation_ir_snapshot(repository_db_path: str) -> None:
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
    presentation_ir = build_presentation_ir_from_legacy_plan(
        plan,
        presentation_id="pres_kr7c",
        snapshot_id="plansnap_ir_kr7c_v1",
        presentation_version_id="presver_kr7c_v1",
        created_from_task_id="task_kr7c_v1",
    )
    presentation_ir["sources"] = [
        {
            "source_id": "sf_source_report",
            "source_type": "stored_file",
            "role": "primary_source",
            "title": "Market report",
            "file_type": "pdf",
            "mime_type": "application/pdf",
            "checksum_sha256": "sourcehash",
            "size_bytes": 4096,
            "extraction_status": "pending",
            "source_file_id": "sf_source_report",
            "provenance_ref": "source_evidence_manifest.json#sf_source_report",
            "storage_uri": "local://secret/source.pdf",
        }
    ]
    service.create_presentation_ir_snapshot(
        presentation_id="pres_kr7c",
        presentation_version_id="presver_kr7c_v1",
        presentation_ir=presentation_ir,
        created_from_task_id="task_kr7c_v1",
        change_summary="Initial native PresentationIR snapshot",
        snapshot_id="plansnap_ir_kr7c_v1",
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
    assert "PresentationApiSourcesResponseSchema" in component_schemas
    assert "PresentationApiSourceRefSchema" in component_schemas
    assert "PresentationIRSnapshotResponseSchema" in component_schemas
    assert "PresentationIRVersionSummarySchema" in component_schemas
    assert "PresentationIRVersionsResponseSchema" in component_schemas
    assert any(tag["name"] == "presentation-api-v1" for tag in schema["tags"])


def test_kr7c_checker_reports_ready() -> None:
    from scripts.kw_presentation_api_contract_check import build_report

    report = build_report()
    assert report["status"] == "ready"
    assert report["missing_paths"] == []
    assert report["missing_legacy_paths"] == []
    assert report["missing_schemas"] == []
    assert report["missing_ir_source_phrases"] == []
    assert report["missing_source_attachment_phrases"] == []


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
    assert payload["ir_schema_version"] == PRESENTATION_IR_SCHEMA_VERSION
    assert payload["storage_format"] == "legacy_plan_snapshot"
    assert payload["version_number"] == 1
    assert len(payload["slides"]) == 7
    assert "storage_uri" not in str(payload)
    assert "local://secret" not in str(payload)


def test_kr7c_gets_versioned_presentation_ir_from_legacy_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_plan_snapshot(repository_db_path)

    response = client.get("/api/v1/presentations/pres_kr7c/ir")

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_version"] == "presentation_api.v1"
    assert payload["ir_schema_version"] == PRESENTATION_IR_SCHEMA_VERSION
    assert payload["storage_format"] == "legacy_plan_snapshot"
    assert payload["version_number"] == 1
    presentation_ir = payload["presentation_ir"]
    assert presentation_ir["schema_version"] == PRESENTATION_IR_SCHEMA_VERSION
    assert presentation_ir["deck"]["presentation_id"] == "pres_kr7c"
    assert presentation_ir["deck"]["slide_count"] == 7
    assert len(presentation_ir["slides"]) == 7


def test_kr7c_persists_native_presentation_ir_and_lists_versions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_native_presentation_ir_snapshot(repository_db_path)

    ir_response = client.get("/api/v1/presentations/pres_kr7c/ir")
    versions_response = client.get("/api/v1/presentations/pres_kr7c/ir/versions")

    assert ir_response.status_code == 200
    ir_payload = ir_response.json()
    assert ir_payload["snapshot_id"] == "plansnap_ir_kr7c_v1"
    assert ir_payload["storage_format"] == "presentation_ir"
    assert ir_payload["presentation_ir"]["schema_version"] == PRESENTATION_IR_SCHEMA_VERSION

    assert versions_response.status_code == 200
    versions_payload = versions_response.json()
    assert versions_payload["ir_schema_version"] == PRESENTATION_IR_SCHEMA_VERSION
    assert versions_payload["versions"] == [
        {
            "snapshot_id": "plansnap_ir_kr7c_v1",
            "presentation_id": "pres_kr7c",
            "presentation_version_id": "presver_kr7c_v1",
            "created_from_task_id": "task_kr7c_v1",
            "change_summary": "Initial native PresentationIR snapshot",
            "created_at": versions_payload["versions"][0]["created_at"],
            "ir_schema_version": PRESENTATION_IR_SCHEMA_VERSION,
            "storage_format": "presentation_ir",
            "version_number": 1,
        }
    ]


def test_kr7c_lists_presentation_source_attachments_from_latest_presentation_ir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_native_presentation_ir_snapshot(repository_db_path)

    response = client.get("/api/v1/presentations/pres_kr7c/sources")

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_version"] == "presentation_api.v1"
    assert payload["presentation_id"] == "pres_kr7c"
    assert payload["snapshot_id"] == "plansnap_ir_kr7c_v1"
    assert payload["ir_schema_version"] == PRESENTATION_IR_SCHEMA_VERSION
    assert payload["storage_format"] == "presentation_ir"
    assert payload["attachment_contract_version"] == PRESENTATION_IR_SOURCE_ATTACHMENT_CONTRACT_VERSION
    assert payload["extraction_runtime_implemented"] is False
    assert payload["sources"] == [
        {
            "source_id": "sf_source_report",
            "source_type": "stored_file",
            "role": "primary_source",
            "title": "Market report",
            "file_type": "pdf",
            "mime_type": "application/pdf",
            "checksum_sha256": "sourcehash",
            "size_bytes": 4096,
            "extraction_status": "pending",
            "source_file_id": "sf_source_report",
            "source_document_id": None,
            "source_presentation_id": None,
            "provenance_ref": "source_evidence_manifest.json#sf_source_report",
        }
    ]
    assert "storage_uri" not in str(payload)
    assert "local://secret" not in str(payload)


def test_kr7c_lists_empty_sources_for_legacy_snapshot_without_extraction_claim(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_plan_snapshot(repository_db_path)

    response = client.get("/api/v1/presentations/pres_kr7c/sources")

    assert response.status_code == 200
    payload = response.json()
    assert payload["storage_format"] == "legacy_plan_snapshot"
    assert payload["sources"] == []
    assert payload["extraction_runtime_implemented"] is False


def test_kr7c_future_mutation_endpoints_fail_closed() -> None:
    create_response = client.post(
        "/api/v1/presentations",
        json={"objective": "Build an executive deck", "slide_count": 6},
    )
    assert create_response.status_code == 501
    assert "KR-7C API-first Presentation contract endpoint" in create_response.json()["detail"]

    source_attach_response = client.post(
        "/api/v1/presentations/pres_kr7c/sources",
        json={"source_file_ids": ["sf_source_report"], "role": "primary_source"},
    )
    assert source_attach_response.status_code == 501

    patch_response = client.patch(
        "/api/v1/presentations/pres_kr7c/slides/slide_001",
        json={"title": "New title", "content": {"bullets": ["A"]}},
    )
    assert patch_response.status_code == 501
