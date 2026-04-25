from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.domain import Presentation, PresentationVersion, StoredFile
from backend.app.main import app
from backend.app.repositories.sqlite import (
    SqlitePresentationPlanSnapshotRepository,
    SqlitePresentationRepository,
    SqlitePresentationVersionRepository,
    SqliteStoredFileRepository,
)
from backend.app.services.slides_service import (
    PresentationPlanSnapshotService,
    deserialize_presentation_plan,
    build_presentation_plan,
)
from backend.app.services.slides_service.outline import PresentationPlan

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


def _register_presentation(
    *,
    repository_db_path: str,
    session_id: str,
    owner_user_id: str = "user_local_default",
    presentation_id: str = "pres_o2",
    file_id: str = "sf_initial_o2",
    version_id: str = "presver_initial_o2",
) -> None:
    stored_files = SqliteStoredFileRepository(repository_db_path)
    presentations = SqlitePresentationRepository(repository_db_path)
    versions = SqlitePresentationVersionRepository(repository_db_path)

    stored_files.create(
        StoredFile(
            id=file_id,
            session_id=session_id,
            task_id="task_initial_o2",
            kind="presentation_deck",
            file_type="pptx",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            title="O2 initial deck",
            original_filename="o2_initial.pptx",
            storage_backend="local",
            storage_key=f"presentations/{session_id}/{file_id}.pptx",
            storage_uri=f"local://presentations/{session_id}/{file_id}.pptx",
            checksum_sha256="initial",
            size_bytes=1024,
            owner_user_id=owner_user_id,
        )
    )
    presentations.create(
        Presentation(
            id=presentation_id,
            session_id=session_id,
            current_file_id=file_id,
            presentation_type="generated_deck",
            title="O2 deck",
        )
    )
    versions.create(
        PresentationVersion(
            id=version_id,
            presentation_id=presentation_id,
            file_id=file_id,
            version_number=1,
            created_from_task_id="task_initial_o2",
            parent_version_id=None,
            change_summary="Initial deck",
        )
    )


def _plan_payload(plan: PresentationPlan) -> dict[str, object]:
    return {
        "deck_title": plan.deck_title,
        "deck_goal": plan.deck_goal,
        "audience": plan.audience,
        "tone": plan.tone,
        "target_slide_count": plan.target_slide_count,
        "story_arc": [stage.value for stage in plan.story_arc],
        "slides": [
            {
                "slide_id": slide.slide_id,
                "slide_type": slide.slide_type.value,
                "story_arc_stage": slide.story_arc_stage.value,
                "title": slide.title,
                "bullets": list(slide.bullets),
                "speaker_notes": slide.speaker_notes,
                "layout_hint": slide.layout_hint,
            }
            for slide in plan.slides
        ],
    }


def _default_plan() -> PresentationPlan:
    return build_presentation_plan(
        "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )


def _seed_plan_snapshot(*, repository_db_path: str, presentation_id: str = "pres_o2") -> None:
    service = PresentationPlanSnapshotService(
        snapshots=SqlitePresentationPlanSnapshotRepository(repository_db_path),
        presentations=SqlitePresentationRepository(repository_db_path),
        presentation_versions=SqlitePresentationVersionRepository(repository_db_path),
    )
    service.create_snapshot(
        presentation_id=presentation_id,
        presentation_version_id="presver_initial_o2",
        plan=_default_plan(),
        created_from_task_id="task_initial_o2",
        change_summary="Initial plan snapshot",
        snapshot_id="plansnap_initial_o2",
    )


def test_o2_slide_revision_without_explicit_plan_loads_latest_snapshot_and_persists_revised_plan(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_plan_snapshot(repository_db_path=repository_db_path)

    response = client.post(
        "/presentations/pres_o2/revisions/slide",
        json={
            "instruction": "Make the analysis slide sharper and more executive.",
            "target_slide_index": 2,
            "task_id": "task_o2_slide_revision",
            "change_summary": "O2 slide revision without explicit plan",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["version_number"] == 2
    assert payload["parent_version_id"] == "presver_initial_o2"
    assert payload["revised_slide_ids"] == ["slide_003"]

    snapshots = SqlitePresentationPlanSnapshotRepository(repository_db_path)
    all_snapshots = snapshots.list_by_presentation("pres_o2")
    assert len(all_snapshots) == 2
    assert all_snapshots[0].id == "plansnap_initial_o2"
    assert all_snapshots[-1].presentation_version_id == payload["version_id"]

    latest_plan = deserialize_presentation_plan(all_snapshots[-1].snapshot_json)
    assert latest_plan.slides[2].slide_id == "slide_003"
    assert "revised:" in latest_plan.slides[2].title
    assert latest_plan.slides[2].speaker_notes is not None
    assert "Make the analysis slide sharper" in latest_plan.slides[2].speaker_notes


def test_o2_section_revision_without_explicit_plan_loads_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    _seed_plan_snapshot(repository_db_path=repository_db_path)

    response = client.post(
        "/presentations/pres_o2/revisions/section",
        json={
            "instruction": "Reframe analysis around delivery risk.",
            "target_stage": "analysis",
            "change_summary": "O2 section revision without explicit plan",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "section"
    assert payload["version_number"] == 2
    assert set(payload["revised_slide_ids"]) == {"slide_003", "slide_006"}

    latest_snapshot = SqlitePresentationPlanSnapshotRepository(repository_db_path).get_latest_for_presentation("pres_o2")
    assert latest_snapshot is not None
    assert latest_snapshot.presentation_version_id == payload["version_id"]


def test_o2_revision_without_plan_fails_clearly_when_snapshot_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)

    response = client.post(
        "/presentations/pres_o2/revisions/slide",
        json={
            "instruction": "Try to revise without a plan snapshot.",
            "target_slide_index": 0,
        },
    )

    assert response.status_code == 409
    assert "no editable plan snapshot" in response.json()["detail"]


def test_o2_explicit_plan_revision_still_works_and_persists_revised_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)

    response = client.post(
        "/presentations/pres_o2/revisions/slide",
        json={
            "instruction": "Explicit plan remains supported.",
            "plan": _plan_payload(_default_plan()),
            "target_slide_index": 1,
            "change_summary": "O2 explicit plan compatibility",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["version_number"] == 2
    assert payload["revised_slide_ids"] == ["slide_002"]

    latest_snapshot = SqlitePresentationPlanSnapshotRepository(repository_db_path).get_latest_for_presentation("pres_o2")
    assert latest_snapshot is not None
    assert latest_snapshot.presentation_version_id == payload["version_id"]


def test_o2_missing_snapshot_error_is_owner_scoped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session(headers={"X-User-Id": "alice"})
    _register_presentation(
        repository_db_path=repository_db_path,
        session_id=session_id,
        owner_user_id="alice",
    )
    _seed_plan_snapshot(repository_db_path=repository_db_path)

    response = client.post(
        "/presentations/pres_o2/revisions/slide",
        headers={"X-User-Id": "bob"},
        json={
            "instruction": "Unauthorized no-plan revision.",
            "target_slide_index": 0,
        },
    )

    assert response.status_code == 404
