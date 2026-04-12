from datetime import datetime, timezone

from backend.app.domain import ArtifactSource, DerivedContent, DocumentVersion, StoredFile
from backend.app.repositories.postgres import (
    PostgresArtifactSourceRepository,
    PostgresDerivedContentRepository,
    PostgresDocumentVersionRepository,
    PostgresStoredFileRepository,
)


class _FakeCursor:
    def __init__(self, store: dict[str, dict[str, dict]]) -> None:
        self._store = store
        self._one = None
        self._many = []

    def execute(self, statement: str, params=None) -> None:
        text = " ".join(statement.split())
        params = params or ()

        if text.startswith("INSERT INTO stored_files"):
            self._store["stored_files"][params[0]] = {
                "id": params[0],
                "session_id": params[1],
                "task_id": params[2],
                "kind": params[3],
                "file_type": params[4],
                "mime_type": params[5],
                "title": params[6],
                "original_filename": params[7],
                "storage_backend": params[8],
                "storage_key": params[9],
                "storage_uri": params[10],
                "checksum_sha256": params[11],
                "size_bytes": params[12],
                "is_remote": params[13],
                "created_at": params[14],
                "updated_at": params[15],
            }
            return
        if text.startswith("SELECT * FROM stored_files WHERE id ="):
            self._one = self._store["stored_files"].get(params[0])
            return
        if text.startswith("SELECT * FROM stored_files WHERE session_id ="):
            self._many = [v for v in self._store["stored_files"].values() if v["session_id"] == params[0]]
            return

        if text.startswith("INSERT INTO document_versions"):
            self._store["document_versions"][params[0]] = {
                "id": params[0],
                "document_id": params[1],
                "file_id": params[2],
                "version_number": params[3],
                "created_from_task_id": params[4],
                "parent_version_id": params[5],
                "change_summary": params[6],
                "created_at": params[7],
            }
            return
        if text.startswith("SELECT * FROM document_versions WHERE document_id ="):
            self._many = [v for v in self._store["document_versions"].values() if v["document_id"] == params[0]]
            self._many.sort(key=lambda item: item["version_number"])
            return

        if text.startswith("INSERT INTO artifact_sources"):
            self._store["artifact_sources"][params[0]] = {
                "id": params[0],
                "artifact_id": params[1],
                "source_file_id": params[2],
                "source_document_id": params[3],
                "source_presentation_id": params[4],
                "role": params[5],
                "created_at": params[6],
            }
            return
        if text.startswith("SELECT * FROM artifact_sources WHERE artifact_id ="):
            self._many = [v for v in self._store["artifact_sources"].values() if v["artifact_id"] == params[0]]
            return

        if text.startswith("INSERT INTO derived_contents"):
            self._store["derived_contents"][params[0]] = {
                "id": params[0],
                "file_id": params[1],
                "content_kind": params[2],
                "text_content": params[3],
                "structured_json": params[4],
                "outline_json": params[5],
                "language": params[6],
                "created_at": params[7],
                "updated_at": params[8],
            }
            return
        if text.startswith("SELECT * FROM derived_contents WHERE file_id ="):
            self._many = [v for v in self._store["derived_contents"].values() if v["file_id"] == params[0]]
            return

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._many

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeConnection:
    def __init__(self, store: dict[str, dict[str, dict]]) -> None:
        self._store = store

    def cursor(self):
        return _FakeCursor(self._store)

    def commit(self) -> None:
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakePsycopg:
    def __init__(self, store: dict[str, dict[str, dict]]) -> None:
        self._store = store

    def connect(self, _dsn: str, row_factory=None):
        return _FakeConnection(self._store)


def test_f4_postgres_repositories_map_metadata_entities(monkeypatch) -> None:
    store = {
        "stored_files": {},
        "document_versions": {},
        "artifact_sources": {},
        "derived_contents": {},
    }
    monkeypatch.setattr("backend.app.repositories.postgres._require_psycopg", lambda: (_FakePsycopg(store), None))

    now = datetime.now(timezone.utc)

    stored_files = PostgresStoredFileRepository("postgresql+psycopg://kw:kw@localhost:5432/kw")
    stored = StoredFile(
        id="file_1",
        session_id="ses_1",
        task_id="task_1",
        kind="generated_artifact",
        file_type="docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        title="Draft",
        original_filename="draft.docx",
        storage_backend="local",
        storage_key="artifacts/ses_1/task_1/file_1/draft.docx",
        storage_uri="local://artifacts/ses_1/task_1/file_1/draft.docx",
        checksum_sha256=None,
        size_bytes=123,
        is_remote=False,
        created_at=now,
        updated_at=now,
    )
    assert stored_files.create(stored) == stored
    assert stored_files.get(stored.id) == stored
    assert [item.id for item in stored_files.list_by_session("ses_1")] == [stored.id]

    document_versions = PostgresDocumentVersionRepository("postgresql+psycopg://kw:kw@localhost:5432/kw")
    dv1 = DocumentVersion(
        id="dv_1",
        document_id="doc_1",
        file_id="file_1",
        version_number=1,
        created_from_task_id="task_1",
        parent_version_id=None,
        change_summary="initial",
        created_at=now,
    )
    dv2 = DocumentVersion(
        id="dv_2",
        document_id="doc_1",
        file_id="file_1",
        version_number=2,
        created_from_task_id="task_2",
        parent_version_id="dv_1",
        change_summary="update",
        created_at=now,
    )
    document_versions.create(dv1)
    document_versions.create(dv2)
    assert [item.version_number for item in document_versions.list_by_document("doc_1")] == [1, 2]

    artifact_sources = PostgresArtifactSourceRepository("postgresql+psycopg://kw:kw@localhost:5432/kw")
    source = ArtifactSource(
        id="as_1",
        artifact_id="art_1",
        source_file_id="file_1",
        source_document_id=None,
        source_presentation_id=None,
        role="primary_source",
        created_at=now,
    )
    artifact_sources.create(source)
    assert [item.id for item in artifact_sources.list_by_artifact("art_1")] == ["as_1"]

    derived_contents = PostgresDerivedContentRepository("postgresql+psycopg://kw:kw@localhost:5432/kw")
    derived = DerivedContent(
        id="dc_1",
        file_id="file_1",
        content_kind="extracted_text",
        text_content="hello",
        structured_json={"a": 1},
        outline_json={"b": 2},
        language="en",
        created_at=now,
        updated_at=now,
    )
    derived_contents.create(derived)
    listed = derived_contents.list_by_file("file_1")
    assert len(listed) == 1
    assert listed[0].id == "dc_1"
