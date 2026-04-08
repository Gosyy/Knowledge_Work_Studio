from __future__ import annotations

from dataclasses import dataclass

from backend.app.domain import TaskType
from backend.app.orchestrator import TaskRouter


@dataclass
class WorkspaceService:
    task_router: TaskRouter

    def resolve_service_key(self, task_type: TaskType) -> str:
        """Thin service-level helper used by API handlers and workers."""
        routed = self.task_router.route(task_type=task_type)
        return routed.service_key
