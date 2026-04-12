from backend.app.integrations.database import bootstrap


class _FakeCursor:
    def __init__(self, statements: list[str]) -> None:
        self._statements = statements
        self._fetchone_result = None

    def execute(self, statement: str, params=None) -> None:
        self._statements.append(statement)
        if "SELECT 1 FROM schema_migrations" in statement:
            self._fetchone_result = None

    def fetchone(self):
        return self._fetchone_result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeConnection:
    def __init__(self, statements: list[str]) -> None:
        self._statements = statements

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self._statements)

    def commit(self) -> None:
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakePsycopg:
    def __init__(self, statements: list[str]) -> None:
        self._statements = statements

    def connect(self, _dsn: str) -> _FakeConnection:
        return _FakeConnection(self._statements)


def test_apply_postgres_baseline_creates_f4_schema_objects(monkeypatch) -> None:
    statements: list[str] = []
    monkeypatch.setattr(bootstrap, "_require_psycopg", lambda: _FakePsycopg(statements))

    bootstrap.apply_postgres_baseline("postgresql+psycopg://kw:kw@localhost:5432/kw")

    sql = "\n".join(statements)

    assert "CREATE TABLE IF NOT EXISTS stored_files" in sql
    assert "CREATE TABLE IF NOT EXISTS documents" in sql
    assert "CREATE TABLE IF NOT EXISTS document_versions" in sql
    assert "CREATE TABLE IF NOT EXISTS presentations" in sql
    assert "CREATE TABLE IF NOT EXISTS presentation_versions" in sql
    assert "CREATE TABLE IF NOT EXISTS artifact_sources" in sql
    assert "CREATE TABLE IF NOT EXISTS derived_contents" in sql

    assert "uq_document_versions_doc_version" in sql
    assert "uq_presentation_versions_presentation_version" in sql
    assert "artifact_sources_at_least_one_source_check" in sql
