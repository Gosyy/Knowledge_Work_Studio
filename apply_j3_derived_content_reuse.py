from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

OLD_UPLOADED = '        content = self._read_text_content(\n            storage_key=uploaded.storage_key,\n            file_type=mirrored_stored_file.file_type,\n            mime_type=uploaded.content_type,\n            source_label=f"uploaded source \'{upload_id}\'",\n        )\n'
NEW_UPLOADED = '        content = self._content_from_stored_file(\n            stored_file=mirrored_stored_file,\n            source_label=f"uploaded source \'{upload_id}\'",\n        )\n'
OLD_CONTENT_METHOD = '    def _content_from_stored_file(\n        self,\n        *,\n        stored_file: StoredFile,\n        source_label: str,\n    ) -> str:\n        return self._read_text_content(\n            storage_key=stored_file.storage_key,\n            file_type=stored_file.file_type,\n            mime_type=stored_file.mime_type,\n            source_label=source_label,\n        )\n'
NEW_CONTENT_METHOD = '    def _content_from_stored_file(\n        self,\n        *,\n        stored_file: StoredFile,\n        source_label: str,\n    ) -> str:\n        cached_text = self._get_cached_extracted_text(stored_file.id)\n        if cached_text is not None:\n            return cached_text\n\n        content = self._read_text_content(\n            storage_key=stored_file.storage_key,\n            file_type=stored_file.file_type,\n            mime_type=stored_file.mime_type,\n            source_label=source_label,\n        )\n        self.derived_contents.create(\n            DerivedContent(\n                id=f"dcon_{uuid4().hex}",\n                file_id=stored_file.id,\n                content_kind="extracted_text",\n                text_content=content,\n                structured_json=None,\n                outline_json=None,\n                language=None,\n            )\n        )\n        return content\n\n    def _get_cached_extracted_text(self, file_id: str) -> str | None:\n        for derived_content in self.derived_contents.list_by_file(file_id):\n            if (\n                derived_content.content_kind == "extracted_text"\n                and derived_content.text_content is not None\n            ):\n                return derived_content.text_content\n        return None\n'
SQLITE_CLASS = '\n\nclass SqliteDerivedContentRepository(_SqliteRepositoryBase):\n    def _initialize_schema(self) -> None:\n        with self._connect() as connection:\n            connection.execute(\n                """\n                CREATE TABLE IF NOT EXISTS derived_contents (\n                    id TEXT PRIMARY KEY,\n                    file_id TEXT NOT NULL,\n                    content_kind TEXT NOT NULL,\n                    text_content TEXT,\n                    structured_json TEXT,\n                    outline_json TEXT,\n                    language TEXT,\n                    created_at TEXT NOT NULL,\n                    updated_at TEXT NOT NULL\n                )\n                """\n            )\n\n    def create(self, derived_content: DerivedContent) -> DerivedContent:\n        with self._lock, self._connect() as connection:\n            connection.execute(\n                """\n                INSERT OR REPLACE INTO derived_contents\n                (id, file_id, content_kind, text_content, structured_json, outline_json, language, created_at, updated_at)\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n                """,\n                (\n                    derived_content.id,\n                    derived_content.file_id,\n                    derived_content.content_kind,\n                    derived_content.text_content,\n                    json.dumps(derived_content.structured_json) if derived_content.structured_json is not None else None,\n                    json.dumps(derived_content.outline_json) if derived_content.outline_json is not None else None,\n                    derived_content.language,\n                    derived_content.created_at.isoformat(),\n                    derived_content.updated_at.isoformat(),\n                ),\n            )\n        return derived_content\n\n    def list_by_file(self, file_id: str) -> list[DerivedContent]:\n        with self._connect() as connection:\n            rows = connection.execute(\n                "SELECT * FROM derived_contents WHERE file_id = ? ORDER BY created_at ASC",\n                (file_id,),\n            ).fetchall()\n        return [\n            DerivedContent(\n                id=row["id"],\n                file_id=row["file_id"],\n                content_kind=row["content_kind"],\n                text_content=row["text_content"],\n                structured_json=json.loads(row["structured_json"]) if row["structured_json"] else None,\n                outline_json=json.loads(row["outline_json"]) if row["outline_json"] else None,\n                language=row["language"],\n                created_at=_parse_datetime(row["created_at"]),\n                updated_at=_parse_datetime(row["updated_at"]),\n            )\n            for row in rows\n        ]\n'
REPO_TEST = 'from datetime import datetime, timezone\nfrom pathlib import Path\n\nfrom backend.app.domain import DerivedContent\nfrom backend.app.repositories.sqlite import SqliteDerivedContentRepository\n\n\ndef test_j3_sqlite_derived_content_repository_persists_extracted_text(tmp_path: Path) -> None:\n    repository = SqliteDerivedContentRepository(str(tmp_path / "derived.sqlite3"))\n    derived_content = DerivedContent(\n        id="dcon_1",\n        file_id="file_1",\n        content_kind="extracted_text",\n        text_content="cached source text",\n        structured_json={"kind": "text"},\n        outline_json=None,\n        language="en",\n        created_at=datetime.now(timezone.utc),\n        updated_at=datetime.now(timezone.utc),\n    )\n\n    repository.create(derived_content)\n\n    assert repository.list_by_file("file_1") == [derived_content]\n'
API_TEST = 'from pathlib import Path\n\nimport pytest\nfrom fastapi.testclient import TestClient\n\nfrom backend.app.core.config import get_settings\nfrom backend.app.main import app\nfrom backend.app.repositories.sqlite import SqliteDerivedContentRepository, SqliteStoredFileRepository\n\nclient = TestClient(app)\n\n\ndef _reset_app_state() -> None:\n    for attribute in (\n        "app_container",\n        "g1_execution_coordinator",\n        "official_execution_coordinator",\n        "llm_provider",\n        "llm_text_service",\n    ):\n        if hasattr(app.state, attribute):\n            delattr(app.state, attribute)\n\n\ndef _configure_sqlite_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> str:\n    repository_db_path = str(tmp_path / "repositories.sqlite3")\n    monkeypatch.setenv("METADATA_BACKEND", "sqlite")\n    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")\n    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))\n    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))\n    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))\n    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))\n    monkeypatch.setenv("REPOSITORY_DB_PATH", repository_db_path)\n    get_settings.cache_clear()\n    _reset_app_state()\n    return repository_db_path\n\n\ndef _create_session_upload_and_task(content: bytes) -> tuple[str, str, str]:\n    session_response = client.post("/sessions", json={})\n    assert session_response.status_code == 201\n    session_id = session_response.json()["id"]\n\n    upload_response = client.post(\n        "/uploads",\n        data={"session_id": session_id},\n        files={"file": ("source.txt", content, "text/plain")},\n    )\n    assert upload_response.status_code == 201\n    upload_id = upload_response.json()["id"]\n\n    task_response = client.post(\n        "/tasks",\n        json={"session_id": session_id, "task_type": "pdf_summary"},\n    )\n    assert task_response.status_code == 201\n    return session_id, upload_id, task_response.json()["id"]\n\n\ndef test_j3_repeated_generation_reuses_cached_derived_content_instead_of_rereading_storage(\n    monkeypatch: pytest.MonkeyPatch,\n    tmp_path: Path,\n) -> None:\n    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)\n    original_text = b"Original first. Original second. Original third."\n    session_id, upload_id, first_task_id = _create_session_upload_and_task(original_text)\n\n    first_response = client.post(\n        f"/tasks/{first_task_id}/execute",\n        json={"uploaded_file_ids": [upload_id]},\n    )\n    assert first_response.status_code == 200\n    assert first_response.json()["result_data"]["output_text"] == "Original first. Original second."\n\n    derived_repository = SqliteDerivedContentRepository(repository_db_path)\n    derived_rows = derived_repository.list_by_file(upload_id)\n    assert len(derived_rows) == 1\n    assert derived_rows[0].content_kind == "extracted_text"\n    assert derived_rows[0].text_content == original_text.decode("utf-8")\n\n    stored_file = SqliteStoredFileRepository(repository_db_path).get(upload_id)\n    assert stored_file is not None\n\n    # Mutate the binary storage layer after extraction. A second generation from\n    # the same source must reuse derived_contents, proving repeated parsing/read\n    # work has been reduced by the metadata model.\n    app.state.app_container.task_source_service.storage.save_bytes(\n        storage_key=stored_file.storage_key,\n        content=b"Changed first. Changed second. Changed third.",\n    )\n\n    second_task_response = client.post(\n        "/tasks",\n        json={"session_id": session_id, "task_type": "pdf_summary"},\n    )\n    assert second_task_response.status_code == 201\n    second_task_id = second_task_response.json()["id"]\n\n    second_response = client.post(\n        f"/tasks/{second_task_id}/execute",\n        json={"uploaded_file_ids": [upload_id]},\n    )\n    assert second_response.status_code == 200\n    second_payload = second_response.json()\n\n    assert second_payload["result_data"]["output_text"] == "Original first. Original second."\n    assert "Changed first" not in second_payload["result_data"]["output_text"]\n    assert len(derived_repository.list_by_file(upload_id)) == 1\n'


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


def patch_task_source_service() -> None:
    rel = "backend/app/services/task_source_service.py"
    text = read(rel)

    text = text.replace(
        "from backend.app.domain import ArtifactSource, Document, Presentation, StoredFile, UploadedFile\n",
        "from backend.app.domain import ArtifactSource, DerivedContent, Document, Presentation, StoredFile, UploadedFile\n",
    )
    text = text.replace(
        "    ArtifactSourceRepository,\n    DocumentRepository,\n",
        "    ArtifactSourceRepository,\n    DerivedContentRepository,\n    DocumentRepository,\n",
    )
    text = text.replace(
        "    presentations: PresentationRepository\n    artifact_sources: ArtifactSourceRepository\n    storage: FileStorage\n",
        "    presentations: PresentationRepository\n    artifact_sources: ArtifactSourceRepository\n    derived_contents: DerivedContentRepository\n    storage: FileStorage\n",
    )
    if OLD_UPLOADED not in text:
        raise SystemExit("[FAIL] uploaded-source read path drifted")
    text = text.replace(OLD_UPLOADED, NEW_UPLOADED)
    if OLD_CONTENT_METHOD not in text:
        raise SystemExit("[FAIL] stored-file content path drifted")
    text = text.replace(OLD_CONTENT_METHOD, NEW_CONTENT_METHOD)
    write(rel, text)


def patch_sqlite_repository() -> None:
    rel = "backend/app/repositories/sqlite.py"
    text = read(rel)
    if "    DerivedContent,\n" not in text:
        text = text.replace("    ArtifactSource,\n", "    ArtifactSource,\n    DerivedContent,\n")
    if "class SqliteDerivedContentRepository" not in text:
        text += SQLITE_CLASS
    write(rel, text)


def patch_repository_exports() -> None:
    rel = "backend/app/repositories/__init__.py"
    text = read(rel)
    if "SqliteDerivedContentRepository" not in text:
        text = text.replace(
            "    SqliteArtifactRepository,\n    SqliteSessionRepository,\n",
            "    SqliteArtifactRepository,\n    SqliteDerivedContentRepository,\n    SqliteSessionRepository,\n",
        )
        text = text.replace(
            '    "SqliteArtifactRepository",\n',
            '    "SqliteArtifactRepository",\n    "SqliteDerivedContentRepository",\n',
        )
    write(rel, text)


def patch_dependencies() -> None:
    rel = "backend/app/api/dependencies.py"
    text = read(rel)
    text = text.replace(
        "    PostgresArtifactSourceRepository,\n    PostgresDocumentRepository,\n",
        "    PostgresArtifactSourceRepository,\n    PostgresDerivedContentRepository,\n    PostgresDocumentRepository,\n",
    )
    text = text.replace(
        "    SqliteArtifactSourceRepository,\n    SqliteDocumentRepository,\n",
        "    SqliteArtifactSourceRepository,\n    SqliteDerivedContentRepository,\n    SqliteDocumentRepository,\n",
    )
    text = text.replace(
        """        return (
            PostgresStoredFileRepository(settings.database_url),
            PostgresDocumentRepository(settings.database_url),
            PostgresPresentationRepository(settings.database_url),
            PostgresArtifactSourceRepository(settings.database_url),
        )
""",
        """        return (
            PostgresStoredFileRepository(settings.database_url),
            PostgresDocumentRepository(settings.database_url),
            PostgresPresentationRepository(settings.database_url),
            PostgresArtifactSourceRepository(settings.database_url),
            PostgresDerivedContentRepository(settings.database_url),
        )
""",
    )
    text = text.replace(
        """    return (
        SqliteStoredFileRepository(settings.repository_db_path),
        SqliteDocumentRepository(settings.repository_db_path),
        SqlitePresentationRepository(settings.repository_db_path),
        SqliteArtifactSourceRepository(settings.repository_db_path),
    )
""",
        """    return (
        SqliteStoredFileRepository(settings.repository_db_path),
        SqliteDocumentRepository(settings.repository_db_path),
        SqlitePresentationRepository(settings.repository_db_path),
        SqliteArtifactSourceRepository(settings.repository_db_path),
        SqliteDerivedContentRepository(settings.repository_db_path),
    )
""",
    )
    text = text.replace(
        "        stored_files, documents, presentations, artifact_sources = _build_source_repositories(settings)\n",
        "        stored_files, documents, presentations, artifact_sources, derived_contents = _build_source_repositories(settings)\n",
    )
    text = text.replace(
        """                artifact_sources=artifact_sources,
                storage=storage,
""",
        """                artifact_sources=artifact_sources,
                derived_contents=derived_contents,
                storage=storage,
""",
    )
    write(rel, text)


def main() -> None:
    if not (ROOT / "backend" / "app").exists():
        raise SystemExit("[FAIL] Put this script in repository root and run it from there.")

    patch_task_source_service()
    patch_sqlite_repository()
    patch_repository_exports()
    patch_dependencies()
    write("backend/tests/integrations/test_j3_derived_contents.py", REPO_TEST)
    write("backend/tests/api/test_j3_derived_content_reuse.py", API_TEST)

    print("[DONE] J3 derived content reuse updates applied.")
    print("Run:")
    print("  python -m pytest -q")
    print("  python -m compileall backend")


if __name__ == "__main__":
    main()
