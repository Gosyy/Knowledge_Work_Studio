from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.domain import Presentation, PresentationVersion
from backend.app.repositories.sqlite import (
    SqlitePresentationPlanSnapshotRepository,
    SqlitePresentationRepository,
    SqlitePresentationVersionRepository,
)
from backend.app.services.slides_service import PresentationPlanSnapshotService, build_presentation_plan


def _repositories(db_path: Path) -> tuple[
    SqlitePresentationRepository,
    SqlitePresentationVersionRepository,
    SqlitePresentationPlanSnapshotRepository,
]:
    return (
        SqlitePresentationRepository(str(db_path)),
        SqlitePresentationVersionRepository(str(db_path)),
        SqlitePresentationPlanSnapshotRepository(str(db_path)),
    )


def _seed_presentation(
    *,
    presentations: SqlitePresentationRepository,
    versions: SqlitePresentationVersionRepository,
) -> None:
    presentations.create(
        Presentation(
            id="pres_o1",
            session_id="ses_o1",
            current_file_id="sf_o1_v2",
            presentation_type="generated_deck",
            title="O1 deck",
        )
    )
    versions.create(
        PresentationVersion(
            id="presver_o1_v1",
            presentation_id="pres_o1",
            file_id="sf_o1_v1",
            version_number=1,
            created_from_task_id="task_o1_v1",
            parent_version_id=None,
            change_summary="Initial",
        )
    )
    versions.create(
        PresentationVersion(
            id="presver_o1_v2",
            presentation_id="pres_o1",
            file_id="sf_o1_v2",
            version_number=2,
            created_from_task_id="task_o1_v2",
            parent_version_id="presver_o1_v1",
            change_summary="Revision",
        )
    )


def test_o1_sqlite_plan_snapshots_are_durable_and_latest_is_ordered(tmp_path: Path) -> None:
    db_path = tmp_path / "repositories.sqlite3"
    presentations, versions, snapshots = _repositories(db_path)
    _seed_presentation(presentations=presentations, versions=versions)

    service = PresentationPlanSnapshotService(
        snapshots=snapshots,
        presentations=presentations,
        presentation_versions=versions,
    )

    first_plan = build_presentation_plan("Opening. Context. Analysis. Close.", min_slides=5, max_slides=5)
    second_plan = build_presentation_plan(
        "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )

    first = service.create_snapshot(
        presentation_id="pres_o1",
        presentation_version_id="presver_o1_v1",
        plan=first_plan,
        created_from_task_id="task_o1_v1",
        change_summary="Initial plan snapshot",
        snapshot_id="plansnap_o1_v1",
    )
    second = service.create_snapshot(
        presentation_id="pres_o1",
        presentation_version_id="presver_o1_v2",
        plan=second_plan,
        created_from_task_id="task_o1_v2",
        change_summary="Revision plan snapshot",
        snapshot_id="plansnap_o1_v2",
    )

    assert first.presentation_version_id == "presver_o1_v1"
    assert second.presentation_version_id == "presver_o1_v2"
    assert service.get_latest_snapshot("pres_o1") is not None
    assert service.get_latest_plan("pres_o1").target_slide_count == 7
    assert service.get_plan_for_version("presver_o1_v1").target_slide_count == 5

    presentations_2, versions_2, snapshots_2 = _repositories(db_path)
    service_2 = PresentationPlanSnapshotService(
        snapshots=snapshots_2,
        presentations=presentations_2,
        presentation_versions=versions_2,
    )

    durable_latest = service_2.get_latest_snapshot("pres_o1")
    assert durable_latest is not None
    assert durable_latest.id == "plansnap_o1_v2"
    assert service_2.get_latest_plan("pres_o1").target_slide_count == 7
    assert service_2.get_snapshot_for_version("presver_o1_v1").id == "plansnap_o1_v1"
    assert [item.id for item in snapshots_2.list_by_presentation("pres_o1")] == ["plansnap_o1_v1", "plansnap_o1_v2"]


def test_o1_plan_snapshot_service_refuses_missing_presentation(tmp_path: Path) -> None:
    db_path = tmp_path / "repositories.sqlite3"
    presentations, versions, snapshots = _repositories(db_path)
    service = PresentationPlanSnapshotService(
        snapshots=snapshots,
        presentations=presentations,
        presentation_versions=versions,
    )

    with pytest.raises(ValueError, match="not found"):
        service.create_snapshot(
            presentation_id="missing",
            plan=build_presentation_plan("Opening. Close."),
        )


def test_o1_plan_snapshot_service_refuses_unknown_version(tmp_path: Path) -> None:
    db_path = tmp_path / "repositories.sqlite3"
    presentations, versions, snapshots = _repositories(db_path)
    _seed_presentation(presentations=presentations, versions=versions)
    service = PresentationPlanSnapshotService(
        snapshots=snapshots,
        presentations=presentations,
        presentation_versions=versions,
    )

    with pytest.raises(ValueError, match="version"):
        service.create_snapshot(
            presentation_id="pres_o1",
            presentation_version_id="missing_version",
            plan=build_presentation_plan("Opening. Close."),
        )
