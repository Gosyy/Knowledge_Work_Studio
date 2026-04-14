from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

from backend.app.domain import LLMRun


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


class SqliteLLMRunRepository:
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
                CREATE TABLE IF NOT EXISTS llm_runs (
                    id TEXT PRIMARY KEY,
                    task_id TEXT,
                    workflow TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    system_prompt TEXT,
                    response_text TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    error_message TEXT,
                    raw_json TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT
                )
                """
            )

    def create(self, llm_run: LLMRun) -> LLMRun:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO llm_runs
                (id, task_id, workflow, provider, model, prompt, system_prompt, response_text,
                 status, error_message, raw_json, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    llm_run.id,
                    llm_run.task_id,
                    llm_run.workflow,
                    llm_run.provider,
                    llm_run.model,
                    llm_run.prompt,
                    llm_run.system_prompt,
                    llm_run.response_text,
                    llm_run.status,
                    llm_run.error_message,
                    json.dumps(llm_run.raw_json) if llm_run.raw_json is not None else None,
                    llm_run.started_at.isoformat(),
                    llm_run.completed_at.isoformat() if llm_run.completed_at else None,
                ),
            )
        return llm_run

    def get(self, llm_run_id: str) -> LLMRun | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM llm_runs WHERE id = ?", (llm_run_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_llm_run(row)

    def list_by_task(self, task_id: str) -> list[LLMRun]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM llm_runs WHERE task_id = ? ORDER BY started_at ASC",
                (task_id,),
            ).fetchall()
        return [self._row_to_llm_run(row) for row in rows]

    def list_by_workflow(self, workflow: str) -> list[LLMRun]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM llm_runs WHERE workflow = ? ORDER BY started_at ASC",
                (workflow,),
            ).fetchall()
        return [self._row_to_llm_run(row) for row in rows]

    @staticmethod
    def _row_to_llm_run(row: sqlite3.Row) -> LLMRun:
        return LLMRun(
            id=row["id"],
            task_id=row["task_id"],
            workflow=row["workflow"],
            provider=row["provider"],
            model=row["model"],
            prompt=row["prompt"],
            system_prompt=row["system_prompt"],
            response_text=row["response_text"],
            status=row["status"],
            error_message=row["error_message"],
            raw_json=json.loads(row["raw_json"]) if row["raw_json"] else None,
            started_at=_parse_datetime(row["started_at"]),
            completed_at=_parse_datetime(row["completed_at"]) if row["completed_at"] else None,
        )


class PostgresLLMRunRepository:
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
                CREATE TABLE IF NOT EXISTS llm_runs (
                    id TEXT PRIMARY KEY,
                    task_id TEXT,
                    workflow TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    system_prompt TEXT,
                    response_text TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    error_message TEXT,
                    raw_json JSONB,
                    started_at TIMESTAMPTZ NOT NULL,
                    completed_at TIMESTAMPTZ
                )
                """
            )
            connection.commit()

    def create(self, llm_run: LLMRun) -> LLMRun:
        with self._lock, self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO llm_runs
                (id, task_id, workflow, provider, model, prompt, system_prompt, response_text,
                 status, error_message, raw_json, started_at, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    task_id = EXCLUDED.task_id,
                    workflow = EXCLUDED.workflow,
                    provider = EXCLUDED.provider,
                    model = EXCLUDED.model,
                    prompt = EXCLUDED.prompt,
                    system_prompt = EXCLUDED.system_prompt,
                    response_text = EXCLUDED.response_text,
                    status = EXCLUDED.status,
                    error_message = EXCLUDED.error_message,
                    raw_json = EXCLUDED.raw_json,
                    started_at = EXCLUDED.started_at,
                    completed_at = EXCLUDED.completed_at
                """,
                (
                    llm_run.id,
                    llm_run.task_id,
                    llm_run.workflow,
                    llm_run.provider,
                    llm_run.model,
                    llm_run.prompt,
                    llm_run.system_prompt,
                    llm_run.response_text,
                    llm_run.status,
                    llm_run.error_message,
                    json.dumps(llm_run.raw_json) if llm_run.raw_json is not None else None,
                    llm_run.started_at,
                    llm_run.completed_at,
                ),
            )
            connection.commit()
        return llm_run

    def get(self, llm_run_id: str) -> LLMRun | None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM llm_runs WHERE id = %s", (llm_run_id,))
            row = cursor.fetchone()
        if row is None:
            return None
        return LLMRun(**row)

    def list_by_task(self, task_id: str) -> list[LLMRun]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM llm_runs WHERE task_id = %s ORDER BY started_at ASC", (task_id,))
            rows = cursor.fetchall()
        return [LLMRun(**row) for row in rows]

    def list_by_workflow(self, workflow: str) -> list[LLMRun]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM llm_runs WHERE workflow = %s ORDER BY started_at ASC", (workflow,))
            rows = cursor.fetchall()
        return [LLMRun(**row) for row in rows]
