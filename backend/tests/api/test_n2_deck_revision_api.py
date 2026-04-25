from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.domain import Presentation, PresentationVersion, StoredFile
from backend.app.main import app
from backend.app.repositories.sqlite import (
    SqlitePresentationRepository,
    SqlitePresentationVersionRepository,
    SqliteStoredFileRepository,
)
from backend.app.services.slides_service.outline import PresentationPlan, build_presentation_plan

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
    presentation_id: str = "pres_n2",
    file_id: str = "sf_initial_n2",
) -> None:
    stored_files = SqliteStoredFileRepository(repository_db_path)
    presentations = SqlitePresentationRepository(repository_db_path)
    versions = SqlitePresentationVersionRepository(repository_db_path)

    stored_files.create(
        StoredFile(
            id=file_id,
            session_id=session_id,
            task_id="task_initial_n2",
            kind="presentation_deck",
            file_type="pptx",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            title="N2 initial deck",
            original_filename="n2_initial.pptx",
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
            title="N2 deck",
        )
    )
    versions.create(
        PresentationVersion(
            id="presver_initial_n2",
            presentation_id=presentation_id,
            file_id=file_id,
            version_number=1,
            created_from_task_id="task_initial_n2",
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


def _default_plan_payload() -> dict[str, object]:
    plan = build_presentation_plan(
        "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )
    return _plan_payload(plan)


def test_n2_slide_revision_api_creates_new_version_and_updates_current_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)

    response = client.post(
        "/presentations/pres_n2/revisions/slide",
        json={
            "instruction": "Emphasize implementation risk and shorten the recommendation.",
            "plan": _default_plan_payload(),
            "target_slide_index": 2,
            "template_id": "business_clean",
            "task_id": "task_revision_n2",
            "change_summary": "Refresh one slide",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["presentation_id"] == "pres_n2"
    assert payload["version_number"] == 2
    assert payload["parent_version_id"] == "presver_initial_n2"
    assert payload["previous_file_id"] == "sf_initial_n2"
    assert payload["stored_file_id"].startswith("sf_presrev_")
    assert payload["current_file_id"] == payload["stored_file_id"]
    assert payload["scope"] == "slide"
    assert payload["revised_slide_ids"] == ["slide_003"]
    assert payload["change_summary"] == "Refresh one slide"

    presentation = SqlitePresentationRepository(repository_db_path).get("pres_n2")
    assert presentation is not None
    assert presentation.current_file_id == payload["stored_file_id"]

    stored_file = SqliteStoredFileRepository(repository_db_path).get(payload["stored_file_id"])
    assert stored_file is not None
    assert stored_file.kind == "presentation_revision"
    assert stored_file.task_id == "task_revision_n2"


def test_n2_section_revision_api_updates_target_stage_and_lineage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)
    plan_payload = _default_plan_payload()

    response = client.post(
        "/presentations/pres_n2/revisions/section",
        json={
            "instruction": "Reframe this section around delivery readiness.",
            "plan": plan_payload,
            "target_stage": "analysis",
            "change_summary": "Refresh analysis section",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "section"
    assert payload["version_number"] == 2
    assert payload["change_summary"] == "Refresh analysis section"
    assert set(payload["revised_slide_ids"]) == {"slide_003", "slide_006"}

    lineage_response = client.get("/presentations/pres_n2/revisions")
    assert lineage_response.status_code == 200
    lineage = lineage_response.json()
    assert [item["version_number"] for item in lineage] == [1, 2]
    assert lineage[-1]["id"] == payload["version_id"]


def test_n2_revision_api_requires_explicit_plan_payload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)

    response = client.post(
        "/presentations/pres_n2/revisions/slide",
        json={
            "instruction": "Revise without plan.",
            "target_slide_index": 0,
        },
    )

    assert response.status_code == 422


def test_n2_revision_api_returns_400_for_invalid_target(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _register_presentation(repository_db_path=repository_db_path, session_id=session_id)

    response = client.post(
        "/presentations/pres_n2/revisions/slide",
        json={
            "instruction": "Revise an invalid slide.",
            "plan": _default_plan_payload(),
            "target_slide_index": 999,
        },
    )

    assert response.status_code == 400
    assert "out of range" in response.json()["detail"]


def test_n2_revision_api_is_owner_scoped(
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

    response = client.post(
        "/presentations/pres_n2/revisions/slide",
        headers={"X-User-Id": "bob"},
        json={
            "instruction": "Unauthorized revision.",
            "plan": _default_plan_payload(),
            "target_slide_index": 0,
        },
    )

    assert response.status_code == 404


def test_n2_missing_presentation_returns_404(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_sqlite_test_env(monkeypatch, tmp_path)

    response = client.get("/presentations/missing/revisions")

    assert response.status_code == 404
    assert response.json()["detail"] == "Presentation not found"
