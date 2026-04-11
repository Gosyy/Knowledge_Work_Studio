from backend.app.domain import Artifact, Session, Task, TaskStatus, TaskType, UploadedFile
from backend.app.repositories import (
    SqliteArtifactRepository,
    SqliteSessionRepository,
    SqliteTaskRepository,
    SqliteUploadedFileRepository,
)


def test_sqlite_repositories_persist_across_instances(tmp_path) -> None:
    db_path = tmp_path / "repos.sqlite3"

    sessions_writer = SqliteSessionRepository(str(db_path))
    tasks_writer = SqliteTaskRepository(str(db_path))
    artifacts_writer = SqliteArtifactRepository(str(db_path))
    uploads_writer = SqliteUploadedFileRepository(str(db_path))

    session = Session(id="ses_1")
    task = Task(id="task_1", session_id=session.id, task_type=TaskType.PDF_SUMMARY, status=TaskStatus.QUEUED)
    artifact = Artifact(
        id="art_1",
        session_id=session.id,
        task_id=task.id,
        filename="summary.txt",
        content_type="text/plain",
        storage_path="/tmp/storage/artifacts/ses_1/task_1/art_1-summary.txt",
        size_bytes=12,
    )
    upload = UploadedFile(
        id="upl_1",
        session_id=session.id,
        original_filename="source.pdf",
        content_type="application/pdf",
        size_bytes=256,
    )

    sessions_writer.create(session)
    tasks_writer.create(task)
    artifacts_writer.create(artifact)
    uploads_writer.create(upload)

    sessions_reader = SqliteSessionRepository(str(db_path))
    tasks_reader = SqliteTaskRepository(str(db_path))
    artifacts_reader = SqliteArtifactRepository(str(db_path))
    uploads_reader = SqliteUploadedFileRepository(str(db_path))

    assert sessions_reader.get(session.id) == session
    assert tasks_reader.get(task.id) == task
    assert artifacts_reader.get(artifact.id) == artifact
    assert uploads_reader.get(upload.id) == upload

    assert [item.id for item in tasks_reader.list_by_session(session.id)] == [task.id]
    assert [item.id for item in artifacts_reader.list_by_session(session.id)] == [artifact.id]
    assert [item.id for item in uploads_reader.list_by_session(session.id)] == [upload.id]
