from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

TASKS_SCHEMA_OLD = 'class TaskExecuteRequest(BaseModel):\n    content: str | None = None\n    uploaded_file_ids: list[str] = Field(default_factory=list)\n    stored_file_ids: list[str] = Field(default_factory=list)\n    document_ids: list[str] = Field(default_factory=list)\n    presentation_ids: list[str] = Field(default_factory=list)\n\n\nclass TaskSchema(BaseModel):\n'
TASKS_SCHEMA_NEW = 'class TaskExecuteRequest(BaseModel):\n    content: str | None = None\n    uploaded_file_ids: list[str] = Field(default_factory=list)\n    stored_file_ids: list[str] = Field(default_factory=list)\n    document_ids: list[str] = Field(default_factory=list)\n    presentation_ids: list[str] = Field(default_factory=list)\n\n\nclass TaskSemanticExecuteRequest(TaskExecuteRequest):\n    workflow: str = Field(\n        default="summarization",\n        description="Semantic workflow: classification, summarization, rewriting, or outline_generation.",\n    )\n    instruction: str | None = None\n\n\nclass TaskSchema(BaseModel):\n'
ROUTE_INSERT = '\n\n_SUPPORTED_SEMANTIC_WORKFLOWS = {\n    "classification",\n    "summarization",\n    "rewriting",\n    "outline_generation",\n}\n\n\ndef _run_semantic_workflow(\n    *,\n    workflow: str,\n    llm_text_service: LLMTextService,\n    content: str,\n    instruction: str | None,\n    task_id: str,\n) -> str:\n    normalized_workflow = workflow.strip().lower()\n    if normalized_workflow not in _SUPPORTED_SEMANTIC_WORKFLOWS:\n        raise HTTPException(\n            status_code=status.HTTP_400_BAD_REQUEST,\n            detail=(\n                "Unsupported semantic workflow. Expected one of: "\n                + ", ".join(sorted(_SUPPORTED_SEMANTIC_WORKFLOWS))\n            ),\n        )\n\n    if normalized_workflow == "classification":\n        return llm_text_service.classify_task(content, task_id=task_id)\n    if normalized_workflow == "summarization":\n        return llm_text_service.summarize_text(content, task_id=task_id)\n    if normalized_workflow == "rewriting":\n        return llm_text_service.rewrite_text(\n            content,\n            instruction=instruction or "Improve clarity while preserving meaning.",\n            task_id=task_id,\n        )\n    return llm_text_service.generate_outline(content, task_id=task_id)\n\n\n@router.post("/tasks/{task_id}/semantic", response_model=TaskSchema)\ndef execute_semantic_task(\n    task_id: str,\n    semantic_request: TaskSemanticExecuteRequest,\n    service: SessionTaskService = Depends(get_session_task_service),\n    task_source_service: TaskSourceService = Depends(get_task_source_service),\n    llm_text_service: LLMTextService = Depends(get_llm_text_service),\n) -> TaskSchema:\n    task = service.get_task(task_id)\n    resolved_input = task_source_service.build_execution_input(\n        session_id=task.session_id,\n        prompt_content=semantic_request.content,\n        uploaded_file_ids=semantic_request.uploaded_file_ids,\n        stored_file_ids=semantic_request.stored_file_ids,\n        document_ids=semantic_request.document_ids,\n        presentation_ids=semantic_request.presentation_ids,\n    )\n\n    service.mark_task_running(task_id)\n    try:\n        output_text = _run_semantic_workflow(\n            workflow=semantic_request.workflow,\n            llm_text_service=llm_text_service,\n            content=resolved_input.content,\n            instruction=semantic_request.instruction,\n            task_id=task_id,\n        )\n    except Exception as exc:\n        failed = service.mark_task_failed(\n            task_id,\n            error_message=str(exc),\n            result_data={\n                "semantic_workflow": semantic_request.workflow,\n                "source_mode": resolved_input.source_mode,\n                "source_refs": resolved_input.as_result_refs(),\n            },\n        )\n        return _task_to_schema(failed)\n\n    completed = service.mark_task_succeeded(\n        task_id,\n        result_data={\n            "task_type": task.task_type.value,\n            "semantic_workflow": semantic_request.workflow,\n            "output_text": output_text,\n            "source_mode": resolved_input.source_mode,\n            "source_refs": resolved_input.as_result_refs(),\n        },\n    )\n    return _task_to_schema(completed)\n'
I3_TEST = 'from pathlib import Path\n\nimport pytest\nfrom fastapi.testclient import TestClient\n\nfrom backend.app.core.config import get_settings\nfrom backend.app.domain import StoredFile\nfrom backend.app.main import app\nfrom backend.app.repositories import SqliteLLMRunRepository\nfrom backend.app.repositories.sqlite import SqliteStoredFileRepository\n\nclient = TestClient(app)\n\n\ndef _reset_app_state() -> None:\n    for attribute in (\n        "app_container",\n        "g1_execution_coordinator",\n        "official_execution_coordinator",\n        "llm_provider",\n        "llm_text_service",\n    ):\n        if hasattr(app.state, attribute):\n            delattr(app.state, attribute)\n\n\ndef _configure_sqlite_fake_llm_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> str:\n    repository_db_path = str(tmp_path / "repositories.sqlite3")\n    monkeypatch.setenv("METADATA_BACKEND", "sqlite")\n    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")\n    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))\n    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))\n    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))\n    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))\n    monkeypatch.setenv("REPOSITORY_DB_PATH", repository_db_path)\n    monkeypatch.setenv("LLM_PROVIDER", "fake")\n    monkeypatch.setenv("FAKE_LLM_RESPONSE", "semantic-provider-output")\n    get_settings.cache_clear()\n    _reset_app_state()\n    return repository_db_path\n\n\ndef _create_session_and_task(task_type: str = "pdf_summary") -> tuple[str, str]:\n    session_response = client.post("/sessions", json={})\n    assert session_response.status_code == 201\n    session_id = session_response.json()["id"]\n\n    task_response = client.post(\n        "/tasks",\n        json={"session_id": session_id, "task_type": task_type},\n    )\n    assert task_response.status_code == 201\n    return session_id, task_response.json()["id"]\n\n\ndef _assert_single_llm_run(repository_db_path: str, *, task_id: str, workflow: str) -> None:\n    runs = SqliteLLMRunRepository(repository_db_path).list_by_task(task_id)\n    assert len(runs) == 1\n    assert runs[0].task_id == task_id\n    assert runs[0].workflow == workflow\n    assert runs[0].provider == "fake"\n    assert runs[0].status == "succeeded"\n    assert runs[0].response_text == "semantic-provider-output"\n\n\ndef test_i3_prompt_only_semantic_task_uses_provider_and_records_llm_run(\n    monkeypatch: pytest.MonkeyPatch,\n    tmp_path: Path,\n) -> None:\n    repository_db_path = _configure_sqlite_fake_llm_env(monkeypatch, tmp_path)\n    _, task_id = _create_session_and_task()\n\n    response = client.post(\n        f"/tasks/{task_id}/semantic",\n        json={\n            "workflow": "summarization",\n            "content": "Alpha. Beta. Gamma.",\n        },\n    )\n\n    assert response.status_code == 200\n    payload = response.json()\n    assert payload["status"] == "succeeded"\n    assert payload["result_data"]["semantic_workflow"] == "summarization"\n    assert payload["result_data"]["output_text"] == "semantic-provider-output"\n    assert payload["result_data"]["source_mode"] == "prompt_only"\n    assert payload["result_data"]["source_refs"] == []\n    _assert_single_llm_run(repository_db_path, task_id=task_id, workflow="summarization")\n\n\ndef test_i3_uploaded_source_semantic_task_uses_provider_and_records_source_mode(\n    monkeypatch: pytest.MonkeyPatch,\n    tmp_path: Path,\n) -> None:\n    repository_db_path = _configure_sqlite_fake_llm_env(monkeypatch, tmp_path)\n    session_id, task_id = _create_session_and_task()\n\n    upload_response = client.post(\n        "/uploads",\n        data={"session_id": session_id},\n        files={"file": ("notes.txt", b"Draft text from upload.", "text/plain")},\n    )\n    assert upload_response.status_code == 201\n    upload_id = upload_response.json()["id"]\n\n    response = client.post(\n        f"/tasks/{task_id}/semantic",\n        json={\n            "workflow": "rewriting",\n            "instruction": "Make it formal.",\n            "uploaded_file_ids": [upload_id],\n        },\n    )\n\n    assert response.status_code == 200\n    payload = response.json()\n    assert payload["status"] == "succeeded"\n    assert payload["result_data"]["semantic_workflow"] == "rewriting"\n    assert payload["result_data"]["source_mode"] == "uploaded_source"\n    assert payload["result_data"]["source_refs"] == [\n        {"kind": "uploaded_file", "source_id": upload_id, "role": "primary_source"}\n    ]\n    _assert_single_llm_run(repository_db_path, task_id=task_id, workflow="rewriting")\n\n\ndef test_i3_stored_source_semantic_task_uses_provider_and_records_source_mode(\n    monkeypatch: pytest.MonkeyPatch,\n    tmp_path: Path,\n) -> None:\n    repository_db_path = _configure_sqlite_fake_llm_env(monkeypatch, tmp_path)\n    session_id, task_id = _create_session_and_task()\n\n    assert hasattr(app.state, "app_container")\n    storage = app.state.app_container.task_source_service.storage\n\n    stored_file_id = "sf_i3_source"\n    storage_key = f"stored/{session_id}/{stored_file_id}/source.txt"\n    storage_uri = storage.save_bytes(\n        storage_key=storage_key,\n        content=b"Stored source for outline.",\n    )\n    SqliteStoredFileRepository(repository_db_path).create(\n        StoredFile(\n            id=stored_file_id,\n            session_id=session_id,\n            task_id=None,\n            kind="uploaded_source",\n            file_type="txt",\n            mime_type="text/plain",\n            title="Stored source",\n            original_filename="source.txt",\n            storage_backend=storage.backend_name,\n            storage_key=storage_key,\n            storage_uri=storage_uri,\n            checksum_sha256=None,\n            size_bytes=len(b"Stored source for outline."),\n        )\n    )\n\n    response = client.post(\n        f"/tasks/{task_id}/semantic",\n        json={\n            "workflow": "outline_generation",\n            "stored_file_ids": [stored_file_id],\n        },\n    )\n\n    assert response.status_code == 200\n    payload = response.json()\n    assert payload["status"] == "succeeded"\n    assert payload["result_data"]["semantic_workflow"] == "outline_generation"\n    assert payload["result_data"]["source_mode"] == "stored_source"\n    assert payload["result_data"]["source_refs"] == [\n        {"kind": "stored_file", "source_id": stored_file_id, "role": "primary_source"}\n    ]\n    _assert_single_llm_run(repository_db_path, task_id=task_id, workflow="outline_generation")\n'


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"[PASS] wrote {rel}")


def replace(rel: str, old: str, new: str) -> None:
    text = read(rel)
    if old not in text:
        raise SystemExit(f"[FAIL] pattern not found in {rel}: {old!r}")
    write(rel, text.replace(old, new))


def main() -> None:
    if not (ROOT / "backend" / "app").exists():
        raise SystemExit("[FAIL] Put this script in repository root and run it from there.")

    if "class TaskSemanticExecuteRequest" not in read("backend/app/api/schemas/tasks.py"):
        replace("backend/app/api/schemas/tasks.py", TASKS_SCHEMA_OLD, TASKS_SCHEMA_NEW)

    schemas_init = read("backend/app/api/schemas/__init__.py")
    if "TaskSemanticExecuteRequest" not in schemas_init:
        replace(
            "backend/app/api/schemas/__init__.py",
            "from backend.app.api.schemas.tasks import TaskCreateRequest, TaskExecuteRequest, TaskSchema\n",
            "from backend.app.api.schemas.tasks import TaskCreateRequest, TaskExecuteRequest, TaskSemanticExecuteRequest, TaskSchema\n",
        )
        replace(
            "backend/app/api/schemas/__init__.py",
            '    "TaskExecuteRequest",\n',
            '    "TaskExecuteRequest",\n    "TaskSemanticExecuteRequest",\n',
        )

    route_text = read("backend/app/api/routes/tasks.py")
    if "get_llm_text_service" not in route_text:
        route_text = route_text.replace(
            """from backend.app.api.dependencies import (
    get_official_execution_coordinator,
    get_session_task_service,
    get_task_source_service,
)
from backend.app.api.schemas import TaskCreateRequest, TaskExecuteRequest, TaskSchema
""",
            """from backend.app.api.dependencies import (
    get_llm_text_service,
    get_official_execution_coordinator,
    get_session_task_service,
    get_task_source_service,
)
from backend.app.api.schemas import TaskCreateRequest, TaskExecuteRequest, TaskSemanticExecuteRequest, TaskSchema
""",
        )
        route_text = route_text.replace(
            "from backend.app.services import SessionTaskService\n",
            "from backend.app.services import LLMTextService, SessionTaskService\n",
        )
    if '"/tasks/{task_id}/semantic"' not in route_text:
        route_text = route_text.replace(
            '\n\n@router.get("/tasks/{task_id}", response_model=TaskSchema)\n',
            ROUTE_INSERT + '\n\n@router.get("/tasks/{task_id}", response_model=TaskSchema)\n',
        )
    write("backend/app/api/routes/tasks.py", route_text)

    write("backend/tests/api/test_i3_semantic_task_sources.py", I3_TEST)

    print("[DONE] I3 source-aware semantic task updates applied.")
    print("Run:")
    print("  python -m pytest -q")
    print("  python -m compileall backend")


if __name__ == "__main__":
    main()
