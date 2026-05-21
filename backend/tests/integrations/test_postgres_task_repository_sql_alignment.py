from threading import Lock

from backend.app.domain import Task, TaskStatus, TaskType
from backend.app.repositories.postgres import PostgresTaskRepository


class _FakeCursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query: str, params: tuple[object, ...] = ()) -> None:
        self.executed.append((query, params))


class _FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = _FakeCursor()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self) -> _FakeCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.committed = True


def _make_repository_without_init(connection: _FakeConnection) -> PostgresTaskRepository:
    repository = PostgresTaskRepository.__new__(PostgresTaskRepository)
    repository._database_url = "postgresql://example"
    repository._lock = Lock()
    repository._connect = lambda: connection  # type: ignore[method-assign]
    return repository


def test_postgres_task_create_keeps_status_and_result_json_sql_placeholders_aligned() -> None:
    connection = _FakeConnection()
    repository = _make_repository_without_init(connection)
    task = Task(
        id="task_sql_alignment",
        session_id="ses_sql_alignment",
        owner_user_id="user_local_default",
        task_type=TaskType.SLIDES_GENERATE,
        status=TaskStatus.PENDING,
        result_data={},
    )

    created = repository.create(task)

    assert created == task
    assert connection.committed is True
    assert len(connection.cursor_instance.executed) == 1
    query, params = connection.cursor_instance.executed[0]
    normalized_query = " ".join(query.split())
    assert "status, result_json" in normalized_query
    assert "VALUES (%s, %s, %s, %s, %s, %s::jsonb" in normalized_query
    assert params[4] == "pending"
    assert params[5] == "{}"
