"""Transitional planning surface kept outside the official execution path.

This module remains available for narrow tests around classification/planning,
but it is not the main supported runtime entrypoint after G1-G3.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.domain import TaskType
from backend.app.orchestrator.classifier import TaskClassifier
from backend.app.orchestrator.planner import ExecutionPlan, TaskPlanner
from backend.app.orchestrator.result_composer import OrchestrationResult, ResultComposer
from backend.app.orchestrator.tool_router import ToolRouter


@dataclass(frozen=True)
class OrchestrationBundle:
    task_type: TaskType
    plan: ExecutionPlan
    tool_keys: tuple[str, ...]


class OrchestrationCoordinator:
    def __init__(
        self,
        classifier: TaskClassifier,
        planner: TaskPlanner,
        tool_router: ToolRouter,
        result_composer: ResultComposer,
    ) -> None:
        self._classifier = classifier
        self._planner = planner
        self._tool_router = tool_router
        self._result_composer = result_composer

    def prepare(self, prompt: str) -> OrchestrationBundle:
        task_type = self._classifier.classify(prompt)
        plan = self._planner.build_plan(task_type)
        tool_keys = self._tool_router.route(task_type)
        return OrchestrationBundle(task_type=task_type, plan=plan, tool_keys=tool_keys)

    def compose_result(self, task_type: TaskType, artifact_ids: list[str]) -> OrchestrationResult:
        return self._result_composer.compose(task_type=task_type, artifact_ids=artifact_ids)
