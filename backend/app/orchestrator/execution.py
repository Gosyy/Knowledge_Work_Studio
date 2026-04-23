from __future__ import annotations

import logging
from dataclasses import dataclass, field

from backend.app.domain import Task, TaskType
from backend.app.orchestrator.router import TaskRouter
from backend.app.services import ArtifactService, DataAnalysisService, SessionTaskService, TaskExecutionService
from backend.app.services.docx_service import DocxServiceEntrypoint, DocxTransformRequest
from backend.app.services.pdf_service import PdfServiceEntrypoint, PdfSummaryRequest
from backend.app.services.slides_service import SlidesGenerateRequest, SlidesServiceEntrypoint

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ServiceExecutionResult:
    output_text: str
    filename: str
    content_type: str
    artifact_content: bytes | None = None
    result_metadata: dict[str, object] = field(default_factory=dict)


class OrchestratorExecutionCoordinator:
    def __init__(
        self,
        *,
        task_router: TaskRouter,
        session_task_service: SessionTaskService,
        task_execution_service: TaskExecutionService,
        artifact_service: ArtifactService,
        data_service: DataAnalysisService,
        docx_service: DocxServiceEntrypoint,
        pdf_service: PdfServiceEntrypoint,
        slides_service: SlidesServiceEntrypoint,
    ) -> None:
        self._task_router = task_router
        self._session_task_service = session_task_service
        self._task_execution_service = task_execution_service
        self._artifact_service = artifact_service
        self._data_service = data_service
        self._docx_service = docx_service
        self._pdf_service = pdf_service
        self._slides_service = slides_service

    def execute_task(self, task_id: str, *, content: str) -> Task:
        logger.info(
            "orchestrator_execute_task",
            extra={
                "task_id": task_id,
                "content_length": len(content),
            },
        )
        return self._task_execution_service.execute(task_id, lambda task: self._run_task(task, content=content))

    def _run_task(self, task: Task, *, content: str) -> dict[str, object]:
        _ = self._task_router.route(task.task_type)
        logger.info(
            "orchestrator_service_dispatch",
            extra={
                "task_id": task.id,
                "task_type": task.task_type.value,
                "content_length": len(content),
            },
        )
        service_result = self._execute_service(task.task_type, content)

        if service_result.artifact_content is None:
            artifact = self._artifact_service.create_placeholder_artifact(
                session_id=task.session_id,
                task_id=task.id,
                filename=service_result.filename,
                content_type=service_result.content_type,
            )
        else:
            artifact = self._artifact_service.create_artifact_from_bytes(
                session_id=task.session_id,
                task_id=task.id,
                filename=service_result.filename,
                content_type=service_result.content_type,
                content=service_result.artifact_content,
            )

        return {
            "task_type": task.task_type.value,
            "output_text": service_result.output_text,
            "artifact_ids": [artifact.id],
            **service_result.result_metadata,
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
                artifact_content=result.artifact_content,
            )

        if task_type is TaskType.PDF_SUMMARY:
            result = self._pdf_service.summarize(PdfSummaryRequest(content=content))
            return ServiceExecutionResult(
                output_text=result.summary,
                filename="summary.txt",
                content_type="text/plain",
                artifact_content=result.artifact_content,
            )

        if task_type is TaskType.DATA_ANALYSIS:
            result = self._data_service.analyze_tabular_content(content=content, file_type="csv")
            return ServiceExecutionResult(
                output_text=result.summary_text,
                filename="analysis.txt",
                content_type="text/plain",
                artifact_content=result.artifact_content,
            )

        if task_type is TaskType.SLIDES_GENERATE:
            result = self._slides_service.generate(SlidesGenerateRequest(content=content))
            return ServiceExecutionResult(
                output_text=result.summary,
                filename="slides.pptx",
                content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                artifact_content=result.artifact_content,
                result_metadata={
                    "outline": [
                        {"title": item.title, "bullets": list(item.bullets)}
                        for item in result.outline
                    ],
                },
            )

        raise ValueError(f"Unsupported task type: {task_type}")
