from __future__ import annotations

from dataclasses import dataclass

from backend.app.domain import Task, TaskType
from backend.app.orchestrator.router import TaskRouter
from backend.app.services import ArtifactService, SessionTaskService, TaskExecutionService
from backend.app.services.docx_service import DocxServiceEntrypoint, DocxTransformRequest
from backend.app.services.pdf_service import PdfServiceEntrypoint, PdfSummaryRequest


@dataclass(frozen=True)
class ServiceExecutionResult:
    output_text: str
    filename: str
    content_type: str


class OrchestratorExecutionCoordinator:
    def __init__(
        self,
        *,
        task_router: TaskRouter,
        session_task_service: SessionTaskService,
        task_execution_service: TaskExecutionService,
        artifact_service: ArtifactService,
        docx_service: DocxServiceEntrypoint,
        pdf_service: PdfServiceEntrypoint,
    ) -> None:
        self._task_router = task_router
        self._session_task_service = session_task_service
        self._task_execution_service = task_execution_service
        self._artifact_service = artifact_service
        self._docx_service = docx_service
        self._pdf_service = pdf_service

    def execute_task(self, task_id: str, *, content: str) -> Task:
        return self._task_execution_service.execute(task_id, lambda task: self._run_task(task, content=content))

    def _run_task(self, task: Task, *, content: str) -> dict[str, object]:
        _ = self._task_router.route(task.task_type)
        service_result = self._execute_service(task.task_type, content)

        artifact = self._artifact_service.create_placeholder_artifact(
            session_id=task.session_id,
            task_id=task.id,
            filename=service_result.filename,
            content_type=service_result.content_type,
        )

        return {
            "task_type": task.task_type.value,
            "output_text": service_result.output_text,
            "artifact_ids": [artifact.id],
        }

    def _execute_service(self, task_type: TaskType, content: str) -> ServiceExecutionResult:
        if task_type is TaskType.DOCX_EDIT:
            result = self._docx_service.transform(
                DocxTransformRequest(content=content, target="draft", replacement="final")
            )
            return ServiceExecutionResult(
                output_text=result.content,
                filename="edited.docx",
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        if task_type is TaskType.PDF_SUMMARY:
            result = self._pdf_service.summarize(PdfSummaryRequest(content=content))
            return ServiceExecutionResult(
                output_text=result.summary,
                filename="summary.txt",
                content_type="text/plain",
            )

        if task_type is TaskType.DATA_ANALYSIS:
            return ServiceExecutionResult(
                output_text="data_analysis_stub_result",
                filename="analysis.txt",
                content_type="text/plain",
            )

        if task_type is TaskType.SLIDES_GENERATE:
            return ServiceExecutionResult(
                output_text="slides_generate_stub_result",
                filename="slides.txt",
                content_type="text/plain",
            )

        raise ValueError(f"Unsupported task type: {task_type}")
