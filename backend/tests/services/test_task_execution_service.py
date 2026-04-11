from backend.app.domain import TaskStatus, TaskType
from backend.app.repositories import InMemorySessionRepository, InMemoryTaskRepository, InMemoryUploadedFileRepository
from backend.app.services import SessionTaskService, TaskExecutionService


class _NoopStorage:
    def save_upload(self, *, session_id: str, upload_id: str, original_filename: str, content: bytes):
        raise NotImplementedError

    def save_artifact(self, *, session_id: str, task_id: str, artifact_id: str, original_filename: str, content: bytes):
        raise NotImplementedError

    def save_temp(self, *, task_id: str, filename: str, content: bytes):
        raise NotImplementedError

    def read_bytes(self, path):
        raise NotImplementedError


def test_task_execution_service_marks_running_then_succeeded_with_result() -> None:
    sessions = InMemorySessionRepository()
    tasks = InMemoryTaskRepository()
    uploads = InMemoryUploadedFileRepository()
    session_task_service = SessionTaskService(sessions=sessions, tasks=tasks, uploads=uploads, storage=_NoopStorage())

    session = session_task_service.create_session()
    task = session_task_service.create_task(session_id=session.id, task_type=TaskType.PDF_SUMMARY)

    execution_service = TaskExecutionService(session_task_service=session_task_service)

    completed = execution_service.execute(task.id, lambda _: {"summary": "done", "pages": 3})

    assert completed.status is TaskStatus.SUCCEEDED
    assert completed.result_data == {"summary": "done", "pages": 3}
    assert completed.started_at is not None
    assert completed.completed_at is not None

    persisted = session_task_service.get_task(task.id)
    assert persisted.status is TaskStatus.SUCCEEDED
    assert persisted.result_data == {"summary": "done", "pages": 3}


def test_task_execution_service_marks_failed_when_runner_raises() -> None:
    sessions = InMemorySessionRepository()
    tasks = InMemoryTaskRepository()
    uploads = InMemoryUploadedFileRepository()
    session_task_service = SessionTaskService(sessions=sessions, tasks=tasks, uploads=uploads, storage=_NoopStorage())

    session = session_task_service.create_session()
    task = session_task_service.create_task(session_id=session.id, task_type=TaskType.DOCX_EDIT)

    execution_service = TaskExecutionService(session_task_service=session_task_service)

    failed = execution_service.execute(task.id, lambda _: (_ for _ in ()).throw(RuntimeError("execution exploded")))

    assert failed.status is TaskStatus.FAILED
    assert failed.error_message == "execution exploded"
    assert failed.started_at is not None
    assert failed.completed_at is not None

    persisted = session_task_service.get_task(task.id)
    assert persisted.status is TaskStatus.FAILED
    assert persisted.error_message == "execution exploded"
