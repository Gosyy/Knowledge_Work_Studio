from __future__ import annotations

from dataclasses import dataclass

from backend.app.domain import TaskType


@dataclass(frozen=True)
class RoutedTask:
    task_type: TaskType
    service_key: str


class TaskRouter:
    """Maps high-level task types to internal service boundaries."""

    _ROUTE_MAP = {
        TaskType.DOCX_EDIT: "docx_service",
        TaskType.PDF_SUMMARY: "pdf_service",
        TaskType.SLIDES_GENERATION: "slides_service",
        TaskType.DATA_ANALYSIS: "data_analysis_service",
    }

    def route(self, task_type: TaskType) -> RoutedTask:
        return RoutedTask(task_type=task_type, service_key=self._ROUTE_MAP[task_type])
