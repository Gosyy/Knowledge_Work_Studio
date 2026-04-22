from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app


def _reset_app_state() -> None:
    for attr in (
        "app_container",
        "official_execution_coordinator",
        "task_queue_service",
        "llm_provider",
        "llm_text_service",
    ):
        if hasattr(app.state, attr):
            delattr(app.state, attr)


def _configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("METADATA_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "storage" / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "storage" / "artifacts"))
    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "storage" / "temp"))
    monkeypatch.setenv("REPOSITORY_DB_PATH", str(tmp_path / "repositories.sqlite3"))
    get_settings.cache_clear()
    _reset_app_state()


def test_m6_openapi_contract_includes_current_mvp_routes(monkeypatch, tmp_path: Path) -> None:
    _configure_test_env(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()

    assert schema["info"]["title"] == "KW Studio API"
    assert "Stable frontend-facing MVP contract" in schema["info"]["description"]

    tag_names = {tag["name"] for tag in schema.get("tags", [])}
    assert {"health", "sessions", "uploads", "tasks", "artifacts"}.issubset(tag_names)

    expected_paths = {
        "/health",
        "/ready",
        "/sessions",
        "/sessions/{session_id}",
        "/uploads",
        "/tasks",
        "/tasks/{task_id}",
        "/tasks/{task_id}/execute",
        "/tasks/{task_id}/semantic",
        "/artifacts/{artifact_id}",
        "/artifacts/{artifact_id}/download",
        "/sessions/{session_id}/artifacts",
    }
    assert expected_paths.issubset(set(schema["paths"].keys()))


def test_m6_openapi_schemas_publish_examples_for_frontend(monkeypatch, tmp_path: Path) -> None:
    _configure_test_env(monkeypatch, tmp_path)

    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    components = schema["components"]["schemas"]
    assert components["SessionCreateRequest"]["example"] == {}
    assert components["TaskCreateRequest"]["example"]["task_type"] == "pdf_summary"
    assert components["TaskExecuteRequest"]["example"]["uploaded_file_ids"] == ["upl_14be29"]
    assert components["TaskSemanticExecuteRequest"]["example"]["workflow"] == "rewriting"
    assert components["TaskSchema"]["example"]["status"] == "succeeded"
    assert components["TaskExecutionJobSchema"]["example"]["status"] == "queued"
    assert components["UploadedFileSchema"]["example"]["storage_backend"] == "local"
    assert components["ArtifactSchema"]["example"]["filename"] == "summary.txt"


def test_m6_frontend_contract_docs_cover_current_mvp_surface() -> None:
    docs = Path("docs/api/frontend_contract.md").read_text(encoding="utf-8")

    required_sections = [
        "GET `/health`",
        "GET `/ready`",
        "POST `/sessions`",
        "POST `/uploads`",
        "POST `/tasks`",
        "POST `/tasks/{task_id}/execute`",
        "POST `/tasks/{task_id}/semantic`",
        "GET `/artifacts/{artifact_id}`",
        "GET `/artifacts/{artifact_id}/download`",
    ]
    for section in required_sections:
        assert section in docs

    assert "NEXT_PUBLIC_API_BASE_URL" in docs
    assert "Response example" in docs
