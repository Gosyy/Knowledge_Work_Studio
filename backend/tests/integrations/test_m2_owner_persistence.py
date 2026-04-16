from backend.app.domain import Artifact, Session, StoredFile, Task, TaskType, UploadedFile
from backend.app.repositories import (
    SqliteArtifactRepository,
    SqliteSessionRepository,
    SqliteTaskRepository,
    SqliteUploadedFileRepository,
)
from backend.app.repositories.sqlite import SqliteStoredFileRepository


def test_m2_sqlite_repositories_persist_owner_fields(tmp_path) -> None:
    db_path = tmp_path / "owners.sqlite3"

    sessions = SqliteSessionRepository(str(db_path))
    tasks = SqliteTaskRepository(str(db_path))
    uploads = SqliteUploadedFileRepository(str(db_path))
    stored_files = SqliteStoredFileRepository(str(db_path))
    artifacts = SqliteArtifactRepository(str(db_path))

    session = Session(id="ses_1", owner_user_id="alice")
    task = Task(id="task_1", session_id=session.id, owner_user_id="alice", task_type=TaskType.PDF_SUMMARY)
    upload = UploadedFile(id="upl_1", session_id=session.id, owner_user_id="alice", original_filename="notes.txt", content_type="text/plain", size_bytes=5)
    stored = StoredFile(
        id=upload.id,
        session_id=session.id,
        task_id=None,
        owner_user_id="alice",
        kind="uploaded_source",
        file_type="txt",
        mime_type="text/plain",
        title="notes.txt",
        original_filename="notes.txt",
        storage_backend="local",
        storage_key="uploads/ses_1/upl_1/notes.txt",
        storage_uri="local://uploads/ses_1/upl_1/notes.txt",
        checksum_sha256=None,
        size_bytes=5,
    )
    artifact = Artifact(id="art_1", session_id=session.id, task_id=task.id, owner_user_id="alice", filename="summary.txt", content_type="text/plain")

    sessions.create(session)
    tasks.create(task)
    uploads.create(upload)
    stored_files.create(stored)
    artifacts.create(artifact)

    assert SqliteSessionRepository(str(db_path)).get(session.id).owner_user_id == "alice"
    assert SqliteTaskRepository(str(db_path)).get(task.id).owner_user_id == "alice"
    assert SqliteUploadedFileRepository(str(db_path)).get(upload.id).owner_user_id == "alice"
    assert SqliteStoredFileRepository(str(db_path)).get(stored.id).owner_user_id == "alice"
    assert SqliteArtifactRepository(str(db_path)).get(artifact.id).owner_user_id == "alice"
