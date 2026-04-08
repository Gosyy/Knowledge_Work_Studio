from __future__ import annotations

from backend.app.domain import TaskType


class ToolRouter:
    _TOOL_MAP: dict[TaskType, tuple[str, ...]] = {
        TaskType.DOCX_EDIT: ("docx_editor",),
        TaskType.PDF_SUMMARY: ("pdf_reader", "summarizer"),
        TaskType.SLIDES_GENERATE: ("slides_builder",),
        TaskType.DATA_ANALYSIS: ("python_kernel", "chart_builder"),
    }

    def route(self, task_type: TaskType) -> tuple[str, ...]:
        return self._TOOL_MAP[task_type]
