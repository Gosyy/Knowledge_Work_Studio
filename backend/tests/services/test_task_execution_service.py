from backend.app.domain import ExecutionRun, TaskStatus, TaskType
from backend.app.repositories import InMemorySessionRepository, InMemoryTaskRepository, InMemoryUploadedFileRepository
from backend.app.services import SessionTaskService, TaskExecutionService


class _NoopStorage:
    backend_name = "test"

    def save_bytes(self, *, storage_key: str, content: bytes, content_type: str | None = None):
        raise NotImplementedError

    def read_bytes(self, *, storage_key: str):
        raise NotImplementedError

    def exists(self, *, storage_key: str) -> bool:
        raise NotImplementedError

    def delete(self, *, storage_key: str) -> None:
        raise NotImplementedError

    def get_size(self, *, storage_key: str) -> int | None:
        raise NotImplementedError

    def make_uri(self, *, storage_key: str) -> str:
        raise NotImplementedError


class _RecordingExecutionRunRepository:
    def __init__(self) -> None:
        self.runs: dict[str, ExecutionRun] = {}

    def create(self, execution_run: ExecutionRun) -> ExecutionRun:
        self.runs[execution_run.id] = execution_run
        return execution_run

    def update(self, execution_run: ExecutionRun) -> ExecutionRun:
        self.runs[execution_run.id] = execution_run
        return execution_run

    def get(self, execution_run_id: str) -> ExecutionRun | None:
        return self.runs.get(execution_run_id)

    def list_by_task(self, task_id: str) -> list[ExecutionRun]:
        return [run for run in self.runs.values() if run.task_id == task_id]


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


def test_h2_task_execution_service_persists_success_execution_run_trace() -> None:
    sessions = InMemorySessionRepository()
    tasks = InMemoryTaskRepository()
    uploads = InMemoryUploadedFileRepository()
    execution_runs = _RecordingExecutionRunRepository()
    session_task_service = SessionTaskService(sessions=sessions, tasks=tasks, uploads=uploads, storage=_NoopStorage())

    session = session_task_service.create_session()
    task = session_task_service.create_task(session_id=session.id, task_type=TaskType.PDF_SUMMARY)

    execution_service = TaskExecutionService(
        session_task_service=session_task_service,
        execution_runs=execution_runs,
    )

    completed = execution_service.execute(task.id, lambda _: {"summary": "done"})

    execution_run_id = completed.result_data["execution_run_id"]
    persisted_runs = execution_runs.list_by_task(task.id)
    assert len(persisted_runs) == 1
    assert persisted_runs[0].id == execution_run_id
    assert persisted_runs[0].task_id == task.id
    assert persisted_runs[0].engine_type == "official_task_execution"
    assert persisted_runs[0].status == "succeeded"
    assert persisted_runs[0].result_json == {"summary": "done"}
    assert persisted_runs[0].error_message is None
    assert persisted_runs[0].started_at is not None
    assert persisted_runs[0].completed_at is not None


def test_h2_task_execution_service_persists_failed_execution_run_trace() -> None:
    sessions = InMemorySessionRepository()
    tasks = InMemoryTaskRepository()
    uploads = InMemoryUploadedFileRepository()
    execution_runs = _RecordingExecutionRunRepository()
    session_task_service = SessionTaskService(sessions=sessions, tasks=tasks, uploads=uploads, storage=_NoopStorage())

    session = session_task_service.create_session()
    task = session_task_service.create_task(session_id=session.id, task_type=TaskType.PDF_SUMMARY)

    execution_service = TaskExecutionService(
        session_task_service=session_task_service,
        execution_runs=execution_runs,
    )

    failed = execution_service.execute(task.id, lambda _: (_ for _ in ()).throw(RuntimeError("boom")))

    execution_run_id = failed.result_data["execution_run_id"]
    persisted_runs = execution_runs.list_by_task(task.id)
    assert len(persisted_runs) == 1
    assert persisted_runs[0].id == execution_run_id
    assert persisted_runs[0].status == "failed"
    assert persisted_runs[0].result_json is None
    assert persisted_runs[0].error_message == "boom"
    assert persisted_runs[0].completed_at is not None
