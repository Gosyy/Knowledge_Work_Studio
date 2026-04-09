from pathlib import Path

from backend.app.core.config import Settings
from backend.app.domain import Session, Task, TaskStatus, TaskType
from backend.app.integrations import get_storage_paths
from backend.app.integrations.database import bootstrap_database
from backend.app.integrations.file_storage import LocalFileStorage
from backend.app.repositories.sqlite import (
    SQLiteSessionRepository,
    SQLiteTaskRepository,
    SQLiteUploadedFileRepository,
)
from backend.app.services.session_task_service import SessionTaskService


def _build_service(tmp_path: Path) -> SessionTaskService:
    db_path = tmp_path / "metadata.sqlite3"
    migrations_dir = Path(__file__).resolve().parents[3] / "scripts" / "migrations"
    database = bootstrap_database(db_path=db_path, migrations_dir=migrations_dir)

    storage_paths = get_storage_paths(
        Settings(
            storage_root=str(tmp_path),
            uploads_dir=str(tmp_path / "uploads"),
            artifacts_dir=str(tmp_path / "artifacts"),
            temp_dir=str(tmp_path / "temp"),
        )
    )

    return SessionTaskService(
        sessions=SQLiteSessionRepository(database),
        tasks=SQLiteTaskRepository(database),
        uploads=SQLiteUploadedFileRepository(database),
        storage=LocalFileStorage(storage_paths),
    )


def test_task_execution_lifecycle_success_persists_result(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    session = service.sessions.create(Session(id="ses_1"))
    task = service.tasks.create(Task(id="task_1", session_id=session.id, task_type=TaskType.PDF_SUMMARY))

    executed = service.execute_task(task.id, executor=lambda _: {"summary": "done", "artifact_ids": ["art_1"]})

    assert executed.status is TaskStatus.SUCCEEDED
    assert executed.result_data == {"summary": "done", "artifact_ids": ["art_1"]}

    persisted = service.get_task(task.id)
    assert persisted.status is TaskStatus.SUCCEEDED
    assert persisted.result_data == {"summary": "done", "artifact_ids": ["art_1"]}


def test_task_execution_lifecycle_failure_persists_error(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    session = service.sessions.create(Session(id="ses_1"))
    task = service.tasks.create(Task(id="task_2", session_id=session.id, task_type=TaskType.DOCX_EDIT))

    def _fail_executor(_: Task) -> dict[str, str]:
        raise RuntimeError("simulated failure")

    executed = service.execute_task(task.id, executor=_fail_executor)

    assert executed.status is TaskStatus.FAILED
    assert executed.result_data == {"error": "simulated failure"}

    persisted = service.get_task(task.id)
    assert persisted.status is TaskStatus.FAILED
    assert persisted.result_data == {"error": "simulated failure"}
