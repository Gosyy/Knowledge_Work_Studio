from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest

from backend.app.domain import Presentation, PresentationVersion, StoredFile
from backend.app.integrations.file_storage.local import LocalFileStorage
from backend.app.integrations.storage import StoragePaths
from backend.app.repositories.postgres import (
    PostgresPresentationPlanSnapshotRepository,
    PostgresPresentationRepository,
    PostgresPresentationVersionRepository,
    PostgresStoredFileRepository,
)
from backend.app.services.slides_service import (
    DeckRevisionRequest,
    DeckRevisionService,
    PresentationPlanSnapshotService,
    build_presentation_plan,
    deserialize_presentation_plan,
    serialize_presentation_plan,
)


def _postgres_test_url() -> str:
    database_url = os.getenv("KW_POSTGRES_TEST_DATABASE_URL") or os.getenv("POSTGRES_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip(
            "Postgres integration test skipped: set KW_POSTGRES_TEST_DATABASE_URL or "
            "POSTGRES_TEST_DATABASE_URL to run it."
        )
    try:
        import psycopg  # noqa: F401
    except ImportError:
        pytest.skip("Postgres integration test skipped: psycopg is not installed.")
    return database_url


def _cleanup_postgres_rows(database_url: str, test_token: str) -> None:
    import psycopg

    normalized_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(normalized_url) as connection, connection.cursor() as cursor:
        cleanup_statements = (
            ("DELETE FROM presentation_plan_snapshots WHERE id LIKE %s OR presentation_id LIKE %s", (f"%{test_token}%", f"%{test_token}%")),
            (
                "DELETE FROM presentation_versions WHERE id LIKE %s OR presentation_id LIKE %s OR file_id LIKE %s",
                (f"%{test_token}%", f"%{test_token}%", f"%{test_token}%"),
            ),
            (
                "DELETE FROM presentations WHERE id LIKE %s OR session_id LIKE %s OR current_file_id LIKE %s",
                (f"%{test_token}%", f"%{test_token}%", f"%{test_token}%"),
            ),
            (
                "DELETE FROM stored_files WHERE id LIKE %s OR session_id LIKE %s OR storage_key LIKE %s",
                (f"%{test_token}%", f"%{test_token}%", f"%{test_token}%"),
            ),
        )
        for statement, params in cleanup_statements:
            try:
                cursor.execute(statement, params)
            except Exception:
                connection.rollback()
            else:
                connection.commit()


def _storage(tmp_path: Path) -> LocalFileStorage:
    return LocalFileStorage(
        StoragePaths(
            root=tmp_path / "storage",
            uploads=tmp_path / "storage" / "uploads",
            artifacts=tmp_path / "storage" / "artifacts",
            temp=tmp_path / "storage" / "temp",
        )
    )


def test_o4_postgres_persists_presentation_versions_and_plan_snapshots(tmp_path: Path) -> None:
    database_url = _postgres_test_url()
    token = f"o4_{uuid4().hex}"
    presentation_id = f"pres_{token}"
    version_1_id = f"presver_{token}_v1"
    version_2_id = f"presver_{token}_v2"
    file_1_id = f"sf_{token}_v1"
    file_2_id = f"sf_{token}_v2"

    try:
        presentations = PostgresPresentationRepository(database_url)
        versions = PostgresPresentationVersionRepository(database_url)
        snapshots = PostgresPresentationPlanSnapshotRepository(database_url)

        presentations.create(
            Presentation(
                id=presentation_id,
                session_id=f"ses_{token}",
                current_file_id=file_2_id,
                presentation_type="generated_deck",
                title="O4 Postgres deck",
            )
        )
        versions.create(
            PresentationVersion(
                id=version_1_id,
                presentation_id=presentation_id,
                file_id=file_1_id,
                version_number=1,
                created_from_task_id=f"task_{token}_v1",
                parent_version_id=None,
                change_summary="Initial Postgres version",
            )
        )
        versions.create(
            PresentationVersion(
                id=version_2_id,
                presentation_id=presentation_id,
                file_id=file_2_id,
                version_number=2,
                created_from_task_id=f"task_{token}_v2",
                parent_version_id=version_1_id,
                change_summary="Second Postgres version",
            )
        )

        snapshot_service = PresentationPlanSnapshotService(
            snapshots=snapshots,
            presentations=presentations,
            presentation_versions=versions,
        )
        plan_v1 = build_presentation_plan("Opening. Context. Analysis. Close.", min_slides=5, max_slides=5)
        plan_v2 = build_presentation_plan(
            "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
            min_slides=7,
            max_slides=7,
        )

        snapshot_service.create_snapshot(
            presentation_id=presentation_id,
            presentation_version_id=version_1_id,
            plan=plan_v1,
            created_from_task_id=f"task_{token}_v1",
            change_summary="Initial Postgres plan",
            snapshot_id=f"plansnap_{token}_v1",
        )
        snapshot_service.create_snapshot(
            presentation_id=presentation_id,
            presentation_version_id=version_2_id,
            plan=plan_v2,
            created_from_task_id=f"task_{token}_v2",
            change_summary="Second Postgres plan",
            snapshot_id=f"plansnap_{token}_v2",
        )

        persisted_versions = versions.list_by_presentation(presentation_id)
        assert [version.id for version in persisted_versions] == [version_1_id, version_2_id]
        assert persisted_versions[1].parent_version_id == version_1_id

        latest_snapshot = snapshot_service.get_latest_snapshot(presentation_id)
        assert latest_snapshot is not None
        assert latest_snapshot.id == f"plansnap_{token}_v2"
        assert latest_snapshot.presentation_version_id == version_2_id
        assert snapshot_service.get_plan_for_version(version_1_id).target_slide_count == 5
        assert snapshot_service.get_latest_plan(presentation_id).target_slide_count == 7
    finally:
        _cleanup_postgres_rows(database_url, token)


def test_o4_postgres_revision_service_persists_lineage_and_revised_plan_snapshot(tmp_path: Path) -> None:
    database_url = _postgres_test_url()
    token = f"o4_{uuid4().hex}"
    session_id = f"ses_{token}"
    presentation_id = f"pres_{token}"
    initial_file_id = f"sf_{token}_initial"
    initial_version_id = f"presver_{token}_initial"

    try:
        storage = _storage(tmp_path)
        stored_files = PostgresStoredFileRepository(database_url)
        presentations = PostgresPresentationRepository(database_url)
        versions = PostgresPresentationVersionRepository(database_url)
        snapshots = PostgresPresentationPlanSnapshotRepository(database_url)

        storage_key = f"presentations/{session_id}/{presentation_id}/initial.pptx"
        stored_files.create(
            StoredFile(
                id=initial_file_id,
                session_id=session_id,
                task_id=f"task_{token}_initial",
                kind="presentation_deck",
                file_type="pptx",
                mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                title="O4 initial deck",
                original_filename="o4_initial.pptx",
                storage_backend=storage.backend_name,
                storage_key=storage_key,
                storage_uri=storage.make_uri(storage_key=storage_key),
                checksum_sha256="initial",
                size_bytes=32,
                owner_user_id="o4_user",
            )
        )
        presentations.create(
            Presentation(
                id=presentation_id,
                session_id=session_id,
                current_file_id=initial_file_id,
                presentation_type="generated_deck",
                title="O4 revision deck",
            )
        )
        versions.create(
            PresentationVersion(
                id=initial_version_id,
                presentation_id=presentation_id,
                file_id=initial_file_id,
                version_number=1,
                created_from_task_id=f"task_{token}_initial",
                parent_version_id=None,
                change_summary="Initial revision lineage",
            )
        )

        plan = build_presentation_plan(
            "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
            min_slides=7,
            max_slides=7,
        )
        snapshot_service = PresentationPlanSnapshotService(
            snapshots=snapshots,
            presentations=presentations,
            presentation_versions=versions,
        )
        snapshot_service.create_snapshot(
            presentation_id=presentation_id,
            presentation_version_id=initial_version_id,
            plan=plan,
            created_from_task_id=f"task_{token}_initial",
            change_summary="Initial plan snapshot",
            snapshot_id=f"plansnap_{token}_initial",
        )

        revision_service = DeckRevisionService(
            storage=storage,
            stored_files=stored_files,
            presentations=presentations,
            presentation_versions=versions,
        )
        result = revision_service.regenerate_slide(
            DeckRevisionRequest(
                presentation_id=presentation_id,
                plan=plan,
                instruction="Make the analysis slide more operationally grounded.",
                task_id=f"task_{token}_revision",
                owner_user_id="o4_user",
                target_slide_index=2,
                change_summary="O4 Postgres slide revision",
            )
        )
        revised_snapshot = snapshot_service.create_snapshot(
            presentation_id=presentation_id,
            presentation_version_id=result.version.id,
            plan=result.revised_plan,
            created_from_task_id=f"task_{token}_revision",
            change_summary="O4 revised plan snapshot",
            snapshot_id=f"plansnap_{token}_revised",
        )

        persisted_presentation = presentations.get(presentation_id)
        assert persisted_presentation is not None
        assert persisted_presentation.current_file_id == result.stored_file.id

        persisted_file = stored_files.get(result.stored_file.id)
        assert persisted_file is not None
        assert persisted_file.kind == "presentation_revision"
        assert storage.exists(storage_key=persisted_file.storage_key)

        lineage = versions.list_by_presentation(presentation_id)
        assert [version.version_number for version in lineage] == [1, 2]
        assert lineage[-1].id == result.version.id
        assert lineage[-1].parent_version_id == initial_version_id

        persisted_revised_snapshot = snapshots.get(revised_snapshot.id)
        assert persisted_revised_snapshot is not None
        assert persisted_revised_snapshot.presentation_version_id == result.version.id
        latest_plan = deserialize_presentation_plan(persisted_revised_snapshot.snapshot_json)
        assert latest_plan.slides[2].slide_id == "slide_003"
        assert "revised:" in latest_plan.slides[2].title
        assert serialize_presentation_plan(latest_plan)["schema_version"] == 1
    finally:
        _cleanup_postgres_rows(database_url, token)
