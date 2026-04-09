from __future__ import annotations

from dataclasses import dataclass

from backend.app.domain import TaskType
from backend.app.runtime.browser.interface import BrowserRuntimeInterface
from backend.app.runtime.kernel.interface import KernelRuntimeInterface
from backend.app.services.docx_service.entrypoint import DocxServiceEntrypoint, DocxTransformRequest
from backend.app.services.pdf_service.entrypoint import PdfServiceEntrypoint, PdfSummaryRequest


@dataclass(frozen=True)
class ServiceExecutionResult:
    output_text: str
    filename: str
    content_type: str


@dataclass
class OrchestratorIntegrationSurface:
    docx: DocxServiceEntrypoint
    pdf: PdfServiceEntrypoint
    kernel: KernelRuntimeInterface
    browser: BrowserRuntimeInterface

    def execute_task(self, task_type: TaskType, content: str) -> ServiceExecutionResult:
        if task_type is TaskType.DOCX_EDIT:
            result = self.docx.transform(DocxTransformRequest(content=content, target="draft", replacement="final"))
            return ServiceExecutionResult(
                output_text=result.content,
                filename="edited.docx",
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        if task_type is TaskType.PDF_SUMMARY:
            result = self.pdf.summarize(PdfSummaryRequest(content=content))
            return ServiceExecutionResult(
                output_text=result.summary,
                filename="summary.txt",
                content_type="text/plain",
            )

        if task_type is TaskType.DATA_ANALYSIS:
            return ServiceExecutionResult(
                output_text="data_analysis_stub_executed",
                filename="analysis.txt",
                content_type="text/plain",
            )

        if task_type is TaskType.SLIDES_GENERATE:
            return ServiceExecutionResult(
                output_text="slides_generate_stub_executed",
                filename="slides.txt",
                content_type="text/plain",
            )

        raise ValueError(f"Unsupported task type: {task_type}")

    def preview_task_execution(self, task_type: TaskType, content: str) -> str:
        """Minimal integration hook for orchestrator wiring tests.

        This intentionally avoids full workflow execution.
        """
        return self.execute_task(task_type=task_type, content=content).output_text
