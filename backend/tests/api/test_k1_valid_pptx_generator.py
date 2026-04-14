from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, is_zipfile

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app

client = TestClient(app)


def _reset_app_state() -> None:
    for attribute in (
        "app_container",
        "g1_execution_coordinator",
        "official_execution_coordinator",
        "llm_provider",
        "llm_text_service",
    ):
        if hasattr(app.state, attribute):
            delattr(app.state, attribute)


def _configure_sqlite_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))
    monkeypatch.setenv("REPOSITORY_DB_PATH", str(tmp_path / "repositories.sqlite3"))
    get_settings.cache_clear()
    _reset_app_state()


def test_k1_slides_generate_official_flow_returns_valid_pptx(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_sqlite_test_env(monkeypatch, tmp_path)

    session_response = client.post("/sessions", json={})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    task_response = client.post(
        "/tasks",
        json={"session_id": session_id, "task_type": "slides_generate"},
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    execute_response = client.post(
        f"/tasks/{task_id}/execute",
        json={"content": "Intro slide. Problem statement. Proposed solution."},
    )
    assert execute_response.status_code == 200
    payload = execute_response.json()
    assert payload["status"] == "succeeded"
    assert payload["result_data"]["task_type"] == "slides_generate"
    artifact_id = payload["result_data"]["artifact_ids"][0]

    artifact_response = client.get(f"/artifacts/{artifact_id}")
    assert artifact_response.status_code == 200
    artifact = artifact_response.json()
    assert artifact["filename"] == "slides.pptx"
    assert artifact["content_type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    assert artifact["size_bytes"] > 0

    download_response = client.get(f"/artifacts/{artifact_id}/download")
    assert download_response.status_code == 200
    pptx_bytes = download_response.content
    assert is_zipfile(BytesIO(pptx_bytes))

    with ZipFile(BytesIO(pptx_bytes)) as pptx:
        names = set(pptx.namelist())
        assert "[Content_Types].xml" in names
        assert "_rels/.rels" in names
        assert "ppt/presentation.xml" in names
        assert "ppt/_rels/presentation.xml.rels" in names
        assert "ppt/slides/slide1.xml" in names
        assert "ppt/slides/_rels/slide1.xml.rels" in names
        assert "ppt/slideMasters/slideMaster1.xml" in names
        assert "ppt/slideLayouts/slideLayout1.xml" in names
        assert "ppt/theme/theme1.xml" in names
        assert not any(name.endswith(".txt") for name in names)
        assert "presentationml.presentation.main+xml" in pptx.read("[Content_Types].xml").decode("utf-8")
