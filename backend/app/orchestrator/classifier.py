from __future__ import annotations

from backend.app.domain import TaskType


class TaskClassifier:
    """Simple deterministic classifier for the orchestrator skeleton."""

    def classify(self, prompt: str) -> TaskType:
        normalized = prompt.lower()
        if "docx" in normalized or "word" in normalized:
            return TaskType.DOCX_EDIT
        if "pdf" in normalized or "summar" in normalized:
            return TaskType.PDF_SUMMARY
        if "slide" in normalized or "deck" in normalized or "ppt" in normalized:
            return TaskType.SLIDES_GENERATE
        if "data" in normalized or "csv" in normalized or "xlsx" in normalized:
            return TaskType.DATA_ANALYSIS
        raise ValueError("Unsupported task type")
