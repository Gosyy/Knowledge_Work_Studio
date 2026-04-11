from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from backend.app.domain import Task
from backend.app.services.session_task_service import SessionTaskService


@dataclass
class TaskExecutionService:
    session_task_service: SessionTaskService

    def execute(self, task_id: str, runner: Callable[[Task], dict[str, Any]]) -> Task:
        running_task = self.session_task_service.mark_task_running(task_id)
        try:
            result_data = runner(running_task)
        except Exception as exc:  # deliberately captures runner failures with explicit lifecycle handling
            return self.session_task_service.mark_task_failed(task_id, error_message=str(exc))
        return self.session_task_service.mark_task_succeeded(task_id, result_data=result_data)
