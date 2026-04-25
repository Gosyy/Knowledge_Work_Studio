from __future__ import annotations

from pathlib import Path

from backend.app.domain import Presentation, PresentationVersion, StoredFile
from backend.app.integrations.file_storage.local import LocalFileStorage
from backend.app.integrations.storage import StoragePaths
from backend.app.repositories.sqlite import (
    SqlitePresentationRepository,
    SqlitePresentationVersionRepository,
    SqliteStoredFileRepository,
)
from backend.app.services.slides_service import (
    DeckRevisionRequest,
    DeckRevisionService,
    StoryArcStage,
    build_presentation_plan,
)


_PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def _storage(tmp_path: Path) -> LocalFileStorage:
    return LocalFileStorage(
        StoragePaths(
            root=tmp_path / "storage",
            uploads=tmp_path / "storage" / "uploads",
            artifacts=tmp_path / "storage" / "artifacts",
            temp=tmp_path / "storage" / "temp",
        )
    )


def _repositories(db_path: Path) -> tuple[
    SqliteStoredFileRepository,
    SqlitePresentationRepository,
    SqlitePresentationVersionRepository,
]:
    return (
        SqliteStoredFileRepository(str(db_path)),
        SqlitePresentationRepository(str(db_path)),
        SqlitePresentationVersionRepository(str(db_path)),
    )


def _service(
    *,
    storage: LocalFileStorage,
    stored_files: SqliteStoredFileRepository,
    presentations: SqlitePresentationRepository,
    versions: SqlitePresentationVersionRepository,
) -> DeckRevisionService:
    return DeckRevisionService(
        storage=storage,
        stored_files=stored_files,
        presentations=presentations,
        presentation_versions=versions,
    )


def _seed_initial_deck(
    *,
    storage: LocalFileStorage,
    stored_files: SqliteStoredFileRepository,
    presentations: SqlitePresentationRepository,
    versions: SqlitePresentationVersionRepository,
    session_id: str = "ses_n3",
    presentation_id: str = "pres_n3",
    file_id: str = "sf_initial_n3",
) -> Presentation:
    initial_key = f"presentations/{session_id}/{presentation_id}/initial/{file_id}.pptx"
    initial_bytes = b"initial-pptx-placeholder"
    storage_uri = storage.save_bytes(
        storage_key=initial_key,
        content=initial_bytes,
        content_type=_PPTX_MIME,
    )

    stored_files.create(
        StoredFile(
            id=file_id,
            session_id=session_id,
            task_id="task_initial_n3",
            kind="presentation_deck",
            file_type="pptx",
            mime_type=_PPTX_MIME,
            title="N3 initial deck",
            original_filename="n3_initial.pptx",
            storage_backend=storage.backend_name,
            storage_key=initial_key,
            storage_uri=storage_uri,
            checksum_sha256="initial-checksum",
            size_bytes=len(initial_bytes),
            owner_user_id="alice",
        )
    )

    presentation = Presentation(
        id=presentation_id,
        session_id=session_id,
        current_file_id=file_id,
        presentation_type="generated_deck",
        title="N3 deck",
    )
    presentations.create(presentation)

    versions.create(
        PresentationVersion(
            id="presver_initial_n3",
            presentation_id=presentation_id,
            file_id=file_id,
            version_number=1,
            created_from_task_id="task_initial_n3",
            parent_version_id=None,
            change_summary="Initial deck",
        )
    )
    return presentation


def test_n3_slide_revision_persists_file_version_and_lineage_across_service_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "repositories.sqlite3"
    storage = _storage(tmp_path)
    stored_files, presentations, versions = _repositories(db_path)
    _seed_initial_deck(
        storage=storage,
        stored_files=stored_files,
        presentations=presentations,
        versions=versions,
    )

    service = _service(
        storage=storage,
        stored_files=stored_files,
        presentations=presentations,
        versions=versions,
    )
    plan = build_presentation_plan(
        "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )

    result = service.regenerate_slide(
        DeckRevisionRequest(
            presentation_id="pres_n3",
            plan=plan,
            target_slide_index=2,
            instruction="Persist this revised analysis slide with stronger implementation risk.",
            task_id="task_revision_n3",
            owner_user_id="alice",
            change_summary="Persisted slide revision",
        )
    )

    assert result.version.version_number == 2
    assert result.version.parent_version_id == "presver_initial_n3"
    assert result.previous_file_id == "sf_initial_n3"
    assert result.stored_file.id.startswith("sf_presrev_")
    assert result.stored_file.kind == "presentation_revision"
    assert result.stored_file.task_id == "task_revision_n3"
    assert result.stored_file.owner_user_id == "alice"

    persisted_file = stored_files.get(result.stored_file.id)
    assert persisted_file == result.stored_file
    assert storage.exists(storage_key=result.stored_file.storage_key)
    assert storage.read_bytes(storage_key=result.stored_file.storage_key).startswith(b"PK")

    persisted_presentation = presentations.get("pres_n3")
    assert persisted_presentation is not None
    assert persisted_presentation.current_file_id == result.stored_file.id

    lineage = versions.list_by_presentation("pres_n3")
    assert [version.version_number for version in lineage] == [1, 2]
    assert lineage[-1].id == result.version.id
    assert lineage[-1].file_id == result.stored_file.id

    # Re-create repositories/service against the same SQLite file to prove durability.
    stored_files_2, presentations_2, versions_2 = _repositories(db_path)
    service_2 = _service(
        storage=storage,
        stored_files=stored_files_2,
        presentations=presentations_2,
        versions=versions_2,
    )

    durable_lineage = service_2.list_revision_lineage("pres_n3")
    durable_presentation = presentations_2.get("pres_n3")
    durable_file = stored_files_2.get(result.stored_file.id)

    assert [version.version_number for version in durable_lineage] == [1, 2]
    assert durable_lineage[-1].id == result.version.id
    assert durable_presentation is not None
    assert durable_presentation.current_file_id == result.stored_file.id
    assert durable_file is not None
    assert storage.read_bytes(storage_key=durable_file.storage_key).startswith(b"PK")


def test_n3_section_revision_increments_version_and_stores_distinct_revision_bytes(tmp_path: Path) -> None:
    db_path = tmp_path / "repositories.sqlite3"
    storage = _storage(tmp_path)
    stored_files, presentations, versions = _repositories(db_path)
    _seed_initial_deck(
        storage=storage,
        stored_files=stored_files,
        presentations=presentations,
        versions=versions,
    )

    service = _service(
        storage=storage,
        stored_files=stored_files,
        presentations=presentations,
        versions=versions,
    )
    plan = build_presentation_plan(
        "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )

    first = service.regenerate_slide(
        DeckRevisionRequest(
            presentation_id="pres_n3",
            plan=plan,
            target_slide_index=2,
            instruction="First persisted slide revision.",
            task_id="task_revision_slide_n3",
            owner_user_id="alice",
        )
    )

    second = service.regenerate_section(
        DeckRevisionRequest(
            presentation_id="pres_n3",
            plan=first.revised_plan,
            target_stage=StoryArcStage.ANALYSIS,
            instruction="Second persisted section revision for all analysis slides.",
            task_id="task_revision_section_n3",
            owner_user_id="alice",
            change_summary="Persisted analysis section revision",
        )
    )

    assert first.version.version_number == 2
    assert second.version.version_number == 3
    assert second.version.parent_version_id == first.version.id
    assert second.previous_file_id == first.stored_file.id
    assert set(second.revised_slide_ids) == {"slide_003", "slide_006"}

    lineage = versions.list_by_presentation("pres_n3")
    assert [version.version_number for version in lineage] == [1, 2, 3]
    assert lineage[-1].id == second.version.id
    assert lineage[-1].change_summary == "Persisted analysis section revision"

    first_file = stored_files.get(first.stored_file.id)
    second_file = stored_files.get(second.stored_file.id)
    assert first_file is not None
    assert second_file is not None
    assert first_file.storage_key != second_file.storage_key
    assert storage.exists(storage_key=first_file.storage_key)
    assert storage.exists(storage_key=second_file.storage_key)
    assert storage.read_bytes(storage_key=first_file.storage_key).startswith(b"PK")
    assert storage.read_bytes(storage_key=second_file.storage_key).startswith(b"PK")

    persisted_presentation = presentations.get("pres_n3")
    assert persisted_presentation is not None
    assert persisted_presentation.current_file_id == second.stored_file.id
