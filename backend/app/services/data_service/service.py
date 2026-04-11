from __future__ import annotations

import json
from dataclasses import dataclass

from backend.app.core.config import Settings
from backend.app.runtime.kernel.interface import KernelRuntimeInterface


@dataclass(frozen=True)
class DataAnalysisResult:
    summary_text: str
    artifact_content: bytes


@dataclass
class DataAnalysisService:
    kernel: KernelRuntimeInterface

    @classmethod
    def from_settings(cls, settings: Settings) -> "DataAnalysisService":
        return cls(kernel=KernelRuntimeInterface.from_settings(settings))

    def analyze_tabular_content(self, *, content: str, file_type: str = "csv") -> DataAnalysisResult:
        session_id = self.kernel.create_session()
        try:
            payload = json.dumps({"file_type": file_type, "content": content})
            result = self.kernel.execute_with_result(
                session_id=session_id,
                code=f"DATA_ANALYSIS::{payload}",
                timeout_seconds=30,
            )
        finally:
            self.kernel.shutdown_session(session_id)

        summary = result.output_text or "No analysis output generated."
        return DataAnalysisResult(summary_text=summary, artifact_content=summary.encode("utf-8"))
