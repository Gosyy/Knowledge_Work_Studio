from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from backend.app.domain import ExecutionRun, Task
from backend.app.repositories import ExecutionRunRepository
from backend.app.services.session_task_service import SessionTaskService

logger = logging.getLogger(__name__)


@dataclass
class TaskExecutionService:
    session_task_service: SessionTaskService
    execution_runs: ExecutionRunRepository | None = None
    engine_type: str = "official_task_execution"

    def execute(self, task_id: str, runner: Callable[[Task], dict[str, Any]]) -> Task:
        running_task = self.session_task_service.mark_task_running(task_id)
        execution_run = self._start_execution_run(running_task)
        logger.info(
            "task_execution_started",
            extra={
                "task_id": task_id,
                "engine_type": self.engine_type,
                "execution_run_id": execution_run.id if execution_run else None,
            },
        )
        try:
            result_data = runner(running_task)
        except Exception as exc:  # deliberately captures runner failures with explicit lifecycle handling
            self._finish_execution_run(
                execution_run=execution_run,
                status="failed",
                result_json=None,
                error_message=str(exc),
            )
            failed_result_data = {"execution_run_id": execution_run.id} if execution_run else None
            logger.error(
                "task_execution_failed",
                extra={
                    "task_id": task_id,
                    "engine_type": self.engine_type,
                    "execution_run_id": execution_run.id if execution_run else None,
                    "error_message": str(exc),
                },
            )
            return self.session_task_service.mark_task_failed(
                task_id,
                error_message=str(exc),
                result_data=failed_result_data,
            )

        self._finish_execution_run(
            execution_run=execution_run,
            status="succeeded",
            result_json=result_data,
            error_message=None,
        )
        if execution_run is not None:
            result_data = {**result_data, "execution_run_id": execution_run.id}
        logger.info(
            "task_execution_succeeded",
            extra={
                "task_id": task_id,
                "engine_type": self.engine_type,
                "execution_run_id": execution_run.id if execution_run else None,
                "result_keys": sorted(result_data.keys()),
            },
        )
        return self.session_task_service.mark_task_succeeded(task_id, result_data=result_data)

    def _start_execution_run(self, task: Task) -> ExecutionRun | None:
        if self.execution_runs is None:
            return None
        execution_run = ExecutionRun(
            id=f"exec_{uuid4().hex}",
            task_id=task.id,
            engine_type=self.engine_type,
            status="running",
            stdout_text="",
            stderr_text="",
            result_json=None,
            error_message=None,
            started_at=task.started_at or datetime.now(timezone.utc),
            completed_at=None,
        )
        return self.execution_runs.create(execution_run)

    def _finish_execution_run(
        self,
        *,
        execution_run: ExecutionRun | None,
        status: str,
        result_json: dict[str, Any] | None,
        error_message: str | None,
    ) -> None:
        if self.execution_runs is None or execution_run is None:
            return
        self.execution_runs.update(
            ExecutionRun(
                id=execution_run.id,
                task_id=execution_run.task_id,
                engine_type=execution_run.engine_type,
                status=status,
                stdout_text=execution_run.stdout_text,
                stderr_text=execution_run.stderr_text,
                result_json=result_json,
                error_message=error_message,
                started_at=execution_run.started_at,
                completed_at=datetime.now(timezone.utc),
            )
        )
