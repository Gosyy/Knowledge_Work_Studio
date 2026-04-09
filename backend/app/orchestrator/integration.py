from __future__ import annotations

from dataclasses import dataclass

from backend.app.domain import TaskType
from backend.app.runtime.browser.interface import BrowserRuntimeInterface
from backend.app.runtime.kernel.interface import KernelRuntimeInterface
from backend.app.services.docx_service.entrypoint import DocxServiceEntrypoint, DocxTransformRequest
from backend.app.services.pdf_service.entrypoint import PdfServiceEntrypoint, PdfSummaryRequest


@dataclass
class OrchestratorIntegrationSurface:
    docx: DocxServiceEntrypoint
    pdf: PdfServiceEntrypoint
    kernel: KernelRuntimeInterface
    browser: BrowserRuntimeInterface

    def preview_task_execution(self, task_type: TaskType, content: str) -> str:
        """Minimal integration hook for orchestrator wiring tests.

        This intentionally avoids full workflow execution.
        """
        if task_type is TaskType.DOCX_EDIT:
            result = self.docx.transform(DocxTransformRequest(content=content, target="draft", replacement="final"))
            return result.content

        if task_type is TaskType.PDF_SUMMARY:
            result = self.pdf.summarize(PdfSummaryRequest(content=content))
            return result.summary

        if task_type is TaskType.DATA_ANALYSIS:
            return "data_analysis_pending"

        if task_type is TaskType.SLIDES_GENERATE:
            return "slides_generate_pending"

        raise ValueError(f"Unsupported task type: {task_type}")
