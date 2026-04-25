from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.api.schemas import (
    SlidesTaskResultDataSchema,
    SourceGroundingMetadataSchema,
    normalize_public_task_result_data,
)
from backend.app.core.config import get_settings
from backend.app.domain import StoredFile
from backend.app.main import app
from backend.app.repositories.sqlite import SqliteStoredFileRepository

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


def _create_slides_task(session_id: str) -> str:
    response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "slides_generate"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_n6_slides_generate_result_data_uses_stable_public_schema(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    task_id = _create_slides_task(session_id)

    response = client.post(
        f"/tasks/{task_id}/execute",
        json={
            "content": "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        },
    )

    assert response.status_code == 200
    result_data = response.json()["result_data"]

    parsed = SlidesTaskResultDataSchema.model_validate(result_data)
    assert parsed.task_type == "slides_generate"
    assert parsed.artifact_ids
    assert parsed.slide_count == len(parsed.outline)
    assert parsed.outline
    assert parsed.generated_media_file_ids == [item.stored_file_id for item in parsed.generated_media_refs]
    assert parsed.source_grounding_metadata is not None
    assert parsed.source_grounding_metadata.citation_count == 0

    serialized = normalize_public_task_result_data(result_data)
    assert "storage_key" not in str(serialized)
    assert "storage_uri" not in str(serialized)


def test_n6_source_grounded_slides_result_data_has_typed_citations(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)
    session_id = _create_session()
    task_id = _create_slides_task(session_id)

    # Build the app container before using its storage.
    assert hasattr(app.state, "app_container")

    storage = app.state.app_container.task_source_service.storage
    storage.save_bytes(
        storage_key="stored/sf_n6_source.txt",
        content=b"Alpha evidence. Beta evidence. Gamma evidence.",
        content_type="text/plain",
    )

    stored_files = SqliteStoredFileRepository(repository_db_path)
    stored_files.create(
        StoredFile(
            id="sf_n6_source",
            session_id=session_id,
            task_id=None,
            kind="uploaded_source",
            file_type="txt",
            mime_type="text/plain",
            title="N6 source",
            original_filename="n6_source.txt",
            storage_backend="local",
            storage_key="stored/sf_n6_source.txt",
            storage_uri="local://stored/sf_n6_source.txt",
            checksum_sha256=None,
            size_bytes=43,
            owner_user_id="user_local_default",
        )
    )

    response = client.post(
        f"/tasks/{task_id}/execute",
        json={"stored_file_ids": ["sf_n6_source"]},
    )

    assert response.status_code == 200
    result_data = response.json()["result_data"]
    parsed = SlidesTaskResultDataSchema.model_validate(result_data)

    assert parsed.source_mode == "stored_source"
    assert parsed.source_refs
    assert parsed.source_grounding_metadata is not None
    assert parsed.source_grounding_metadata.citation_count > 0
    assert parsed.source_grounding_metadata.citations[0].source_id == "sf_n6_source"
    assert parsed.source_grounding_metadata.citations[0].derived_content_id is not None


def test_n6_source_grounding_metadata_schema_rejects_unknown_storage_fields() -> None:
    with pytest.raises(ValueError, match="extra_forbidden"):
        SourceGroundingMetadataSchema.model_validate(
            {
                "citation_count": 1,
                "citations": [
                    {
                        "citation_id": "cite_1",
                        "source_kind": "stored_file",
                        "source_id": "sf_1",
                        "fragment_id": "frag_1",
                        "source_label": "stored_file/sf_1",
                        "excerpt": "Alpha",
                        "storage_uri": "local://unsafe",
                    }
                ],
            }
        )


def test_n6_public_result_data_normalization_rejects_unsafe_storage_keys() -> None:
    with pytest.raises(ValueError, match="Unsafe slides API metadata key"):
        normalize_public_task_result_data(
            {
                "task_type": "slides_generate",
                "output_text": "Generated 1 slide.",
                "artifact_ids": ["art_1"],
                "outline": [{"title": "Slide", "bullets": ["A"]}],
                "storage_key": "unsafe/internal/path.pptx",
            }
        )


def test_n6_public_result_data_normalization_preserves_legacy_media_ids() -> None:
    result_data = normalize_public_task_result_data(
        {
            "task_type": "slides_generate",
            "output_text": "Generated 1 slide.",
            "artifact_ids": ["art_1"],
            "outline": [{"title": "Slide", "bullets": ["A"]}],
            "generated_media_file_ids": ["sf_img_1"],
        }
    )

    parsed = SlidesTaskResultDataSchema.model_validate(result_data)
    assert parsed.generated_media_file_ids == ["sf_img_1"]
    assert parsed.generated_media_refs[0].stored_file_id == "sf_img_1"
