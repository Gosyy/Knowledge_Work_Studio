from datetime import datetime, timezone
from pathlib import Path

from backend.app.domain import Artifact, Session, Task, TaskStatus, TaskType, UploadedFile
from backend.app.integrations.database import bootstrap_database
from backend.app.repositories.sqlite import (
    SQLiteArtifactRepository,
    SQLiteSessionRepository,
    SQLiteTaskRepository,
    SQLiteUploadedFileRepository,
)


def _build_repositories(db_path: Path) -> tuple[
    SQLiteSessionRepository,
    SQLiteTaskRepository,
    SQLiteArtifactRepository,
    SQLiteUploadedFileRepository,
]:
    migrations_dir = Path(__file__).resolve().parents[3] / "scripts" / "migrations"
    database = bootstrap_database(db_path=db_path, migrations_dir=migrations_dir)
    return (
        SQLiteSessionRepository(database),
        SQLiteTaskRepository(database),
        SQLiteArtifactRepository(database),
        SQLiteUploadedFileRepository(database),
    )


def test_sqlite_repositories_persist_across_reinstantiation(tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite3"
    sessions, tasks, artifacts, uploads = _build_repositories(db_path)

    created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    session = sessions.create(Session(id="ses_1", created_at=created_at))
    task = tasks.create(
        Task(
            id="task_1",
            session_id=session.id,
            task_type=TaskType.PDF_SUMMARY,
            status=TaskStatus.PENDING,
            created_at=created_at,
        )
    )
    artifact = artifacts.create(
        Artifact(
            id="art_1",
            session_id=session.id,
            task_id=task.id,
            filename="summary.txt",
            content_type="text/plain",
            storage_path="/tmp/storage/art_1-summary.txt",
            size_bytes=42,
            created_at=created_at,
        )
    )
    upload = uploads.create(
        UploadedFile(
            id="upl_1",
            session_id=session.id,
            original_filename="source.pdf",
            content_type="application/pdf",
            size_bytes=128,
            created_at=created_at,
        )
    )

    sessions_2, tasks_2, artifacts_2, uploads_2 = _build_repositories(db_path)

    assert sessions_2.get(session.id) == session
    assert tasks_2.get(task.id) == task
    assert tasks_2.list_by_session(session.id) == [task]
    assert artifacts_2.get(artifact.id) == artifact
    assert artifacts_2.list_by_session(session.id) == [artifact]
    assert uploads_2.get(upload.id) == upload
    assert uploads_2.list_by_session(session.id) == [upload]


def test_sqlite_repositories_return_none_for_missing_records(tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite3"
    sessions, tasks, artifacts, uploads = _build_repositories(db_path)

    assert sessions.get("missing") is None
    assert tasks.get("missing") is None
    assert tasks.list_by_session("missing") == []
    assert artifacts.get("missing") is None
    assert artifacts.list_by_session("missing") == []
    assert uploads.get("missing") is None
    assert uploads.list_by_session("missing") == []
