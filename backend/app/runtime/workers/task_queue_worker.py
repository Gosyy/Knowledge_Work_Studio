from __future__ import annotations

from dataclasses import dataclass

from backend.app.domain import TaskExecutionJob
from backend.app.services.task_queue_service import TaskQueueService


@dataclass
class TaskQueueWorker:
    """Worker skeleton for M4 in-process queued execution."""

    queue_service: TaskQueueService

    def run_once(self) -> TaskExecutionJob | None:
        return self.queue_service.process_next()
