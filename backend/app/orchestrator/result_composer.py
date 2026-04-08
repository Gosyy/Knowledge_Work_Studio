from __future__ import annotations

from dataclasses import dataclass

from backend.app.domain import TaskType


@dataclass(frozen=True)
class OrchestrationResult:
    task_type: TaskType
    artifact_ids: tuple[str, ...]
    summary: str


class ResultComposer:
    def compose(self, task_type: TaskType, artifact_ids: list[str]) -> OrchestrationResult:
        return OrchestrationResult(
            task_type=task_type,
            artifact_ids=tuple(artifact_ids),
            summary=f"Prepared {len(artifact_ids)} artifact(s) for task type {task_type.value}",
        )
