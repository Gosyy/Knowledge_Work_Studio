from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, status

from backend.app.domain import TaskExecutionJob, TaskJobStatus, TaskStatus
from backend.app.integrations.queue import TaskExecutionQueue
from backend.app.services.session_task_service import SessionTaskService
from backend.app.services.task_source_service import TaskSourceService



if TYPE_CHECKING:
    from backend.app.orchestrator.execution import OrchestratorExecutionCoordinator

def _not_found(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@dataclass
class TaskQueueService:
    queue: TaskExecutionQueue
    session_task_service: SessionTaskService
    task_source_service: TaskSourceService
    coordinator: "OrchestratorExecutionCoordinator"

    def enqueue_execution(
        self,
        *,
        task_id: str,
        owner_user_id: str,
        payload: dict[str, object],
    ) -> TaskExecutionJob:
        # M4 does not execute here. It only creates an honest queued lifecycle.
        self.session_task_service.get_task_for_user(task_id, owner_user_id)
        return self.queue.enqueue(task_id=task_id, owner_user_id=owner_user_id, payload=payload)

    def get_job_for_user(self, *, job_id: str, owner_user_id: str) -> TaskExecutionJob:
        job = self.queue.get(job_id)
        if job is None or job.owner_user_id != owner_user_id:
            _not_found("Task execution job not found")
        return job

    def process_next(self) -> TaskExecutionJob | None:
        job = self.queue.claim_next()
        if job is None:
            return None
        return self._run_claimed_job(job)

    def process_job_for_user(self, *, job_id: str, owner_user_id: str) -> TaskExecutionJob:
        current = self.get_job_for_user(job_id=job_id, owner_user_id=owner_user_id)
        if current.status is not TaskJobStatus.QUEUED:
            return current
        claimed = self.queue.claim(job_id)
        if claimed is None:
            _not_found("Task execution job not found")
        return self._run_claimed_job(claimed)

    def _run_claimed_job(self, job: TaskExecutionJob) -> TaskExecutionJob:
        try:
            self.session_task_service.get_task_for_user(job.task_id, job.owner_user_id)
            resolved_input = self.task_source_service.build_execution_input(
                session_id=self.session_task_service.get_task(job.task_id).session_id,
                owner_user_id=job.owner_user_id,
                prompt_content=self._payload_text(job.payload, "content"),
                uploaded_file_ids=self._payload_list(job.payload, "uploaded_file_ids"),
                stored_file_ids=self._payload_list(job.payload, "stored_file_ids"),
                document_ids=self._payload_list(job.payload, "document_ids"),
                presentation_ids=self._payload_list(job.payload, "presentation_ids"),
            )

            executed_task = self.coordinator.execute_task(job.task_id, content=resolved_input.content)

            if executed_task.status is not TaskStatus.SUCCEEDED:
                return self.queue.fail(
                    job.id,
                    error_message=executed_task.error_message or f"Task finished with status {executed_task.status.value}",
                )

            artifact_ids = [
                artifact_id
                for artifact_id in executed_task.result_data.get("artifact_ids", [])
                if isinstance(artifact_id, str)
            ]
            self.task_source_service.record_artifact_sources(
                artifact_ids=artifact_ids,
                sources=resolved_input.sources,
            )

            updated_result_data: dict[str, Any] = {
                **executed_task.result_data,
                "source_mode": resolved_input.source_mode,
                "source_refs": resolved_input.as_result_refs(),
                "queued_job_id": job.id,
            }
            self.session_task_service.mark_task_succeeded(job.task_id, result_data=updated_result_data)
            return self.queue.complete(job.id, result_task_id=job.task_id)
        except Exception as exc:
            return self.queue.fail(job.id, error_message=str(exc))

    @staticmethod
    def _payload_text(payload: dict[str, object], key: str) -> str | None:
        value = payload.get(key)
        return value if isinstance(value, str) else None

    @staticmethod
    def _payload_list(payload: dict[str, object], key: str) -> list[str]:
        value = payload.get(key)
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str)]
