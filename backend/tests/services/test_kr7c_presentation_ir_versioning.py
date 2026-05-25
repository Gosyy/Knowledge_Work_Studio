from pathlib import Path

import pytest

from backend.app.domain import Presentation, PresentationVersion, StoredFile
from backend.app.repositories.sqlite import (
    SqlitePresentationPlanSnapshotRepository,
    SqlitePresentationRepository,
    SqlitePresentationVersionRepository,
    SqliteStoredFileRepository,
)
from backend.app.services.slides_service import (
    PRESENTATION_IR_SCHEMA_VERSION,
    PresentationPlanSnapshotService,
    build_presentation_ir_from_legacy_plan,
    build_presentation_plan,
    detect_presentation_ir_storage_format,
    require_presentation_ir_payload,
)


def _build_service(tmp_path: Path) -> PresentationPlanSnapshotService:
    db_path = str(tmp_path / "repositories.sqlite3")
    SqliteStoredFileRepository(db_path).create(
        StoredFile(
            id="sf_ir_contract",
            session_id="ses_ir_contract",
            task_id="task_ir_contract",
            kind="presentation_deck",
            file_type="pptx",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            title="IR contract deck",
            original_filename="ir-contract.pptx",
            storage_backend="local",
            storage_key="presentations/ir/sf_ir_contract.pptx",
            storage_uri="local://presentations/ir/sf_ir_contract.pptx",
            checksum_sha256="ir",
            size_bytes=1024,
        )
    )
    SqlitePresentationRepository(db_path).create(
        Presentation(
            id="pres_ir_contract",
            session_id="ses_ir_contract",
            current_file_id="sf_ir_contract",
            presentation_type="generated_deck",
            title="IR contract deck",
        )
    )
    SqlitePresentationVersionRepository(db_path).create(
        PresentationVersion(
            id="presver_ir_contract_v1",
            presentation_id="pres_ir_contract",
            file_id="sf_ir_contract",
            version_number=1,
            created_from_task_id="task_ir_contract",
            parent_version_id=None,
            change_summary="Initial IR contract deck",
        )
    )
    return PresentationPlanSnapshotService(
        snapshots=SqlitePresentationPlanSnapshotRepository(db_path),
        presentations=SqlitePresentationRepository(db_path),
        presentation_versions=SqlitePresentationVersionRepository(db_path),
    )


def _plan():
    return build_presentation_plan(
        "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )


def test_presentation_ir_payload_validates_and_round_trips_through_snapshot_store(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    presentation_ir = build_presentation_ir_from_legacy_plan(
        _plan(),
        presentation_id="pres_ir_contract",
        snapshot_id="plansnap_ir_contract_v1",
        presentation_version_id="presver_ir_contract_v1",
        created_from_task_id="task_ir_contract",
    )

    snapshot = service.create_presentation_ir_snapshot(
        presentation_id="pres_ir_contract",
        presentation_version_id="presver_ir_contract_v1",
        presentation_ir=presentation_ir,
        created_from_task_id="task_ir_contract",
        change_summary="Persist native PresentationIR",
        snapshot_id="plansnap_ir_contract_v1",
    )

    stored = service.get_latest_snapshot("pres_ir_contract")
    assert stored == snapshot
    assert stored is not None
    assert detect_presentation_ir_storage_format(stored.snapshot_json) == "presentation_ir"
    assert service.get_latest_presentation_ir("pres_ir_contract") == presentation_ir
    assert service.list_ir_snapshot_versions("pres_ir_contract")[0]["ir_schema_version"] == PRESENTATION_IR_SCHEMA_VERSION


def test_legacy_plan_snapshot_is_exposed_as_versioned_presentation_ir(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    service.create_snapshot(
        presentation_id="pres_ir_contract",
        presentation_version_id="presver_ir_contract_v1",
        plan=_plan(),
        created_from_task_id="task_ir_contract",
        change_summary="Persist legacy plan",
        snapshot_id="plansnap_legacy_contract_v1",
    )

    latest = service.get_latest_snapshot("pres_ir_contract")
    assert latest is not None
    assert detect_presentation_ir_storage_format(latest.snapshot_json) == "legacy_plan_snapshot"

    presentation_ir = service.get_presentation_ir_for_snapshot(latest)
    assert presentation_ir["schema_version"] == PRESENTATION_IR_SCHEMA_VERSION
    assert presentation_ir["deck"]["presentation_id"] == "pres_ir_contract"
    assert presentation_ir["quality_contract"]["source_format"] == "legacy_plan_snapshot.v1"
    assert len(presentation_ir["slides"]) == 7


def test_invalid_native_presentation_ir_is_rejected_before_persistence(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    invalid = {"schema_version": PRESENTATION_IR_SCHEMA_VERSION, "deck": {}}

    with pytest.raises(ValueError, match="Invalid PresentationIR payload"):
        require_presentation_ir_payload(invalid)

    with pytest.raises(ValueError, match="Invalid PresentationIR payload"):
        service.create_presentation_ir_snapshot(
            presentation_id="pres_ir_contract",
            presentation_version_id="presver_ir_contract_v1",
            presentation_ir=invalid,
            snapshot_id="plansnap_invalid_ir",
        )
