from __future__ import annotations

from dataclasses import dataclass

from backend.app.domain import TaskType


@dataclass(frozen=True)
class PlanStep:
    key: str
    description: str


@dataclass(frozen=True)
class ExecutionPlan:
    task_type: TaskType
    steps: tuple[PlanStep, ...]


class TaskPlanner:
    def build_plan(self, task_type: TaskType) -> ExecutionPlan:
        return ExecutionPlan(
            task_type=task_type,
            steps=(
                PlanStep(key="ingest", description="Validate inputs and normalize context"),
                PlanStep(key="execute", description="Run domain service"),
                PlanStep(key="finalize", description="Persist artifacts and return metadata"),
            ),
        )
