from __future__ import annotations

from backend.app.repositories.postgres import PostgresSessionRepository


class _StrictCursor:
    def __init__(self, connection: "_StrictConnection") -> None:
        self._connection = connection

    def execute(self, statement: str, params=None) -> None:  # noqa: ANN001 - fake psycopg cursor signature.
        self._connection.events.append(("execute", " ".join(statement.split())))

    def __enter__(self) -> "_StrictCursor":
        self._connection.events.append(("cursor_enter", None))
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001 - context manager protocol.
        self._connection.events.append(("cursor_exit", None))
        return False


class _StrictConnection:
    def __init__(self) -> None:
        self.closed = False
        self.events: list[tuple[str, str | None]] = []

    def cursor(self) -> _StrictCursor:
        return _StrictCursor(self)

    def commit(self) -> None:
        if self.closed:
            raise AssertionError("commit called after the Postgres connection context was closed")
        self.events.append(("commit", None))

    def __enter__(self) -> "_StrictConnection":
        self.events.append(("connection_enter", None))
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001 - context manager protocol.
        self.closed = True
        self.events.append(("connection_exit", None))
        return False


class _StrictPsycopg:
    def __init__(self) -> None:
        self.connections: list[_StrictConnection] = []

    def connect(self, _dsn: str, row_factory=None) -> _StrictConnection:  # noqa: ANN001 - fake psycopg signature.
        connection = _StrictConnection()
        self.connections.append(connection)
        return connection


def test_r1_postgres_session_schema_commit_occurs_before_connection_close(monkeypatch) -> None:
    fake_psycopg = _StrictPsycopg()
    monkeypatch.setattr(
        "backend.app.repositories.postgres._require_psycopg",
        lambda: (fake_psycopg, object()),
    )

    PostgresSessionRepository("postgresql+psycopg://kw:kw@postgres:5432/kwstudio")

    assert len(fake_psycopg.connections) == 1
    events = fake_psycopg.connections[0].events
    assert ("commit", None) in events
    assert ("connection_exit", None) in events
    assert events.index(("commit", None)) < events.index(("connection_exit", None))

    statements = [payload for event, payload in events if event == "execute" and payload is not None]
    assert any("CREATE TABLE IF NOT EXISTS sessions" in statement for statement in statements)
    assert any("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS owner_user_id" in statement for statement in statements)
