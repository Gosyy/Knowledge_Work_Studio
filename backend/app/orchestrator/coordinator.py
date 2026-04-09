from __future__ import annotations

from dataclasses import dataclass

from backend.app.domain import Task, TaskType
from backend.app.orchestrator.classifier import TaskClassifier
from backend.app.orchestrator.integration import OrchestratorIntegrationSurface
from backend.app.orchestrator.planner import ExecutionPlan, TaskPlanner
from backend.app.orchestrator.result_composer import OrchestrationResult, ResultComposer
from backend.app.orchestrator.router import TaskRouter
from backend.app.orchestrator.tool_router import ToolRouter
from backend.app.services import ArtifactService, SessionTaskService


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


class TaskExecutionCoordinator:
    def __init__(
        self,
        *,
        tasks: SessionTaskService,
        artifacts: ArtifactService,
        task_router: TaskRouter,
        integration_surface: OrchestratorIntegrationSurface,
    ) -> None:
        self._tasks = tasks
        self._artifacts = artifacts
        self._task_router = task_router
        self._integration_surface = integration_surface

    def execute_task(self, task_id: str, content: str = "") -> Task:
        task = self._tasks.get_task(task_id)
        routed_task = self._task_router.route(task.task_type)

        def _executor(current_task: Task) -> dict[str, object]:
            execution = self._integration_surface.execute_task(current_task.task_type, content)
            artifact = self._artifacts.create_placeholder_artifact(
                session_id=current_task.session_id,
                task_id=current_task.id,
                filename=execution.filename,
                content_type=execution.content_type,
            )
            return {
                "service_key": routed_task.service_key,
                "output_text": execution.output_text,
                "artifact_ids": [artifact.id],
            }

        return self._tasks.execute_task(task_id=task.id, executor=_executor)
