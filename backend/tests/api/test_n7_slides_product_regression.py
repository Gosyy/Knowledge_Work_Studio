from __future__ import annotations

from io import BytesIO
from pathlib import Path
import zipfile

import pytest
from fastapi.testclient import TestClient

from backend.app.api.schemas import SlidesTaskResultDataSchema
from backend.app.core.config import get_settings
from backend.app.domain import Presentation, PresentationVersion, StoredFile
from backend.app.main import app
from backend.app.repositories.sqlite import (
    SqlitePresentationRepository,
    SqlitePresentationVersionRepository,
    SqliteStoredFileRepository,
)
from backend.app.services.slides_service import PresentationPlan, build_presentation_plan

client = TestClient(app)

_PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


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


def _create_slides_task(session_id: str) -> str:
    response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "slides_generate"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _download_artifact(artifact_id: str) -> bytes:
    response = client.get(f"/artifacts/{artifact_id}/download")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(_PPTX_MIME)
    return response.content


def _assert_valid_pptx(payload: bytes) -> None:
    assert payload.startswith(b"PK")
    with zipfile.ZipFile(BytesIO(payload), "r") as pptx_zip:
        names = set(pptx_zip.namelist())
        assert "[Content_Types].xml" in names
        assert "ppt/presentation.xml" in names
        assert "ppt/slides/slide1.xml" in names
        assert "ppt/theme/theme1.xml" in names


def _all_pptx_xml(payload: bytes) -> str:
    with zipfile.ZipFile(BytesIO(payload), "r") as pptx_zip:
        return "\n".join(
            pptx_zip.read(name).decode("utf-8", errors="replace")
            for name in pptx_zip.namelist()
            if name.endswith(".xml")
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


def _seed_source_file(*, repository_db_path: str, session_id: str, stored_file_id: str = "sf_n7_source") -> None:
    storage_key = f"stored/{stored_file_id}.txt"
    storage = app.state.app_container.task_source_service.storage
    storage.save_bytes(
        storage_key=storage_key,
        content=b"Alpha evidence. Beta evidence. Gamma evidence.",
        content_type="text/plain",
    )

    SqliteStoredFileRepository(repository_db_path).create(
        StoredFile(
            id=stored_file_id,
            session_id=session_id,
            task_id=None,
            kind="uploaded_source",
            file_type="txt",
            mime_type="text/plain",
            title="N7 source",
            original_filename="n7_source.txt",
            storage_backend="local",
            storage_key=storage_key,
            storage_uri=f"local://{storage_key}",
            checksum_sha256=None,
            size_bytes=43,
            owner_user_id="user_local_default",
        )
    )


def _seed_presentation_for_revision(*, repository_db_path: str, session_id: str) -> None:
    stored_files = SqliteStoredFileRepository(repository_db_path)
    presentations = SqlitePresentationRepository(repository_db_path)
    versions = SqlitePresentationVersionRepository(repository_db_path)

    stored_files.create(
        StoredFile(
            id="sf_n7_initial",
            session_id=session_id,
            task_id="task_n7_initial",
            kind="presentation_deck",
            file_type="pptx",
            mime_type=_PPTX_MIME,
            title="N7 initial deck",
            original_filename="n7_initial.pptx",
            storage_backend="local",
            storage_key="presentations/n7/sf_n7_initial.pptx",
            storage_uri="local://presentations/n7/sf_n7_initial.pptx",
            checksum_sha256="initial",
            size_bytes=1024,
            owner_user_id="user_local_default",
        )
    )
    presentations.create(
        Presentation(
            id="pres_n7",
            session_id=session_id,
            current_file_id="sf_n7_initial",
            presentation_type="generated_deck",
            title="N7 deck",
        )
    )
    versions.create(
        PresentationVersion(
            id="presver_n7_initial",
            presentation_id="pres_n7",
            file_id="sf_n7_initial",
            version_number=1,
            created_from_task_id="task_n7_initial",
            parent_version_id=None,
            change_summary="Initial deck",
        )
    )


def test_n7_sync_prompt_only_slides_generation_regression(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    task_id = _create_slides_task(session_id)

    response = client.post(
        f"/tasks/{task_id}/execute",
        json={"content": "Opening. Context. Analysis. Compare. Timeline. Data. Close."},
    )

    assert response.status_code == 200
    result_data = response.json()["result_data"]
    parsed = SlidesTaskResultDataSchema.model_validate(result_data)

    assert parsed.task_type == "slides_generate"
    assert parsed.artifact_ids
    assert parsed.slide_count == len(parsed.outline)
    assert parsed.source_mode == "inline"

    pptx_payload = _download_artifact(parsed.artifact_ids[0])
    _assert_valid_pptx(pptx_payload)


def test_n7_queued_slides_generation_regression(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    task_id = _create_slides_task(session_id)

    enqueue_response = client.post(
        f"/tasks/{task_id}/enqueue",
        json={"content": "Opening. Context. Analysis. Compare. Timeline. Data. Close."},
    )
    assert enqueue_response.status_code == 202
    job_id = enqueue_response.json()["id"]

    run_response = client.post(f"/task-jobs/{job_id}/run")
    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["status"] == "succeeded"
    assert run_payload["result_task_id"] == task_id

    task_response = client.get(f"/tasks/{task_id}")
    assert task_response.status_code == 200
    result_data = task_response.json()["result_data"]
    parsed = SlidesTaskResultDataSchema.model_validate(result_data)

    assert parsed.task_type == "slides_generate"
    assert parsed.artifact_ids
    assert result_data["queued_job_id"] == job_id


def test_n7_source_grounded_slides_generation_regression(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    task_id = _create_slides_task(session_id)
    _seed_source_file(repository_db_path=repository_db_path, session_id=session_id)

    response = client.post(
        f"/tasks/{task_id}/execute",
        json={"stored_file_ids": ["sf_n7_source"]},
    )

    assert response.status_code == 200
    parsed = SlidesTaskResultDataSchema.model_validate(response.json()["result_data"])
    assert parsed.source_mode == "stored_source"
    assert parsed.source_refs
    assert parsed.source_grounding_metadata is not None
    assert parsed.source_grounding_metadata.citation_count > 0
    assert parsed.source_grounding_metadata.citations[0].source_id == "sf_n7_source"


def test_n7_structured_blocks_are_present_in_downloaded_pptx(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    task_id = _create_slides_task(session_id)

    response = client.post(
        f"/tasks/{task_id}/execute",
        json={
            "content": (
                "Executive opening. Market context. Operating model. Compare options. "
                "Delivery timeline. Revenue 10 cost 4 margin 6. Final recommendation."
            )
        },
    )

    assert response.status_code == 200
    parsed = SlidesTaskResultDataSchema.model_validate(response.json()["result_data"])
    pptx_payload = _download_artifact(parsed.artifact_ids[0])
    xml = _all_pptx_xml(pptx_payload)

    assert "comparison_block" in xml
    assert "timeline_block" in xml
    assert "table_block cell" in xml
    assert "chart_block bar" in xml
    assert "business_metric_block card" in xml


def test_n7_presentation_retrieval_and_revision_api_regression(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    _seed_presentation_for_revision(repository_db_path=repository_db_path, session_id=session_id)

    list_response = client.get(f"/sessions/{session_id}/presentations")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == "pres_n7"

    get_response = client.get("/presentations/pres_n7")
    assert get_response.status_code == 200
    assert get_response.json()["current_file_id"] == "sf_n7_initial"

    revision_response = client.post(
        "/presentations/pres_n7/revisions/slide",
        json={
            "instruction": "Revise one slide for N7 regression coverage.",
            "plan": _default_plan_payload(),
            "target_slide_index": 2,
            "task_id": "task_n7_revision",
            "change_summary": "N7 regression revision",
        },
    )
    assert revision_response.status_code == 200
    revision_payload = revision_response.json()
    assert revision_payload["version_number"] == 2
    assert revision_payload["parent_version_id"] == "presver_n7_initial"
    assert revision_payload["previous_file_id"] == "sf_n7_initial"
    assert revision_payload["stored_file_id"].startswith("sf_presrev_")

    lineage_response = client.get("/presentations/pres_n7/revisions")
    assert lineage_response.status_code == 200
    assert [item["version_number"] for item in lineage_response.json()] == [1, 2]

    refreshed_response = client.get("/presentations/pres_n7")
    assert refreshed_response.status_code == 200
    assert refreshed_response.json()["current_file_id"] == revision_payload["stored_file_id"]
