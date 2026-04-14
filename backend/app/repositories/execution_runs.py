from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

from backend.app.domain import ExecutionRun


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _normalize_database_url(database_url: str) -> str:
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def _require_psycopg() -> tuple[Any, Any]:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError(
            "psycopg is required for metadata_backend=postgres. "
            "Install psycopg or use explicit sqlite test mode "
            "(METADATA_BACKEND=sqlite and SQLITE_RUNTIME_ALLOWED=true)."
        ) from exc
    return psycopg, dict_row


class SqliteExecutionRunRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_runs (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    engine_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stdout_text TEXT NOT NULL DEFAULT '',
                    stderr_text TEXT NOT NULL DEFAULT '',
                    result_json TEXT,
                    error_message TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT
                )
                """
            )

    def create(self, execution_run: ExecutionRun) -> ExecutionRun:
        return self._upsert(execution_run)

    def update(self, execution_run: ExecutionRun) -> ExecutionRun:
        return self._upsert(execution_run)

    def _upsert(self, execution_run: ExecutionRun) -> ExecutionRun:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO execution_runs
                (id, task_id, engine_type, status, stdout_text, stderr_text, result_json, error_message, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution_run.id,
                    execution_run.task_id,
                    execution_run.engine_type,
                    execution_run.status,
                    execution_run.stdout_text,
                    execution_run.stderr_text,
                    json.dumps(execution_run.result_json) if execution_run.result_json is not None else None,
                    execution_run.error_message,
                    execution_run.started_at.isoformat(),
                    execution_run.completed_at.isoformat() if execution_run.completed_at else None,
                ),
            )
        return execution_run

    def get(self, execution_run_id: str) -> ExecutionRun | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM execution_runs WHERE id = ?",
                (execution_run_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_execution_run(row)

    def list_by_task(self, task_id: str) -> list[ExecutionRun]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM execution_runs WHERE task_id = ? ORDER BY started_at ASC",
                (task_id,),
            ).fetchall()
        return [self._row_to_execution_run(row) for row in rows]

    @staticmethod
    def _row_to_execution_run(row: sqlite3.Row) -> ExecutionRun:
        return ExecutionRun(
            id=row["id"],
            task_id=row["task_id"],
            engine_type=row["engine_type"],
            status=row["status"],
            stdout_text=row["stdout_text"],
            stderr_text=row["stderr_text"],
            result_json=json.loads(row["result_json"]) if row["result_json"] else None,
            error_message=row["error_message"],
            started_at=_parse_datetime(row["started_at"]),
            completed_at=_parse_datetime(row["completed_at"]) if row["completed_at"] else None,
        )


class PostgresExecutionRunRepository:
    def __init__(self, database_url: str) -> None:
        self._database_url = _normalize_database_url(database_url)
        self._lock = Lock()
        self._initialize_schema()

    def _connect(self):
        psycopg, dict_row = _require_psycopg()
        return psycopg.connect(self._database_url, row_factory=dict_row)

    def _initialize_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_runs (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    engine_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stdout_text TEXT NOT NULL DEFAULT '',
                    stderr_text TEXT NOT NULL DEFAULT '',
                    result_json JSONB,
                    error_message TEXT,
                    started_at TIMESTAMPTZ NOT NULL,
                    completed_at TIMESTAMPTZ
                )
                """
            )
            connection.commit()

    def create(self, execution_run: ExecutionRun) -> ExecutionRun:
        return self._upsert(execution_run)

    def update(self, execution_run: ExecutionRun) -> ExecutionRun:
        return self._upsert(execution_run)

    def _upsert(self, execution_run: ExecutionRun) -> ExecutionRun:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO execution_runs
                (id, task_id, engine_type, status, stdout_text, stderr_text, result_json, error_message, started_at, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    task_id = EXCLUDED.task_id,
                    engine_type = EXCLUDED.engine_type,
                    status = EXCLUDED.status,
                    stdout_text = EXCLUDED.stdout_text,
                    stderr_text = EXCLUDED.stderr_text,
                    result_json = EXCLUDED.result_json,
                    error_message = EXCLUDED.error_message,
                    started_at = EXCLUDED.started_at,
                    completed_at = EXCLUDED.completed_at
                """,
                (
                    execution_run.id,
                    execution_run.task_id,
                    execution_run.engine_type,
                    execution_run.status,
                    execution_run.stdout_text,
                    execution_run.stderr_text,
                    json.dumps(execution_run.result_json) if execution_run.result_json is not None else None,
                    execution_run.error_message,
                    execution_run.started_at,
                    execution_run.completed_at,
                ),
            )
            connection.commit()
        return execution_run

    def get(self, execution_run_id: str) -> ExecutionRun | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM execution_runs WHERE id = %s", (execution_run_id,))
            row = cursor.fetchone()
        if row is None:
            return None
        return ExecutionRun(**row)

    def list_by_task(self, task_id: str) -> list[ExecutionRun]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM execution_runs WHERE task_id = %s ORDER BY started_at ASC", (task_id,))
            rows = cursor.fetchall()
        return [ExecutionRun(**row) for row in rows]
