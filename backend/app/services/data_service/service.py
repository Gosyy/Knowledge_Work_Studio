from __future__ import annotations

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
            result = self.kernel.execute_with_result(
                session_id=session_id,
                code=self._build_analysis_code(content=content, file_type=file_type),
                timeout_seconds=30,
            )
        finally:
            self.kernel.shutdown_session(session_id)

        if result.status != "succeeded":
            summary = result.stderr_text or result.output_text or "Data analysis execution failed."
        else:
            summary = result.output_text or "No analysis output generated."
        return DataAnalysisResult(summary_text=summary, artifact_content=summary.encode("utf-8"))

    @staticmethod
    def _build_analysis_code(*, content: str, file_type: str) -> str:
        # Build plain Python code without nested f-strings.
        # This prevents the outer service-side formatter from evaluating
        # variables that only exist inside the controlled engine subprocess.
        return f"""
import csv
import io

file_type = {file_type!r}
content = {content!r}

if file_type.lower() != "csv":
    raise ValueError("Unsupported data analysis file type: " + file_type)

rows = list(csv.reader(io.StringIO(content)))
if not rows:
    result = "No rows detected in dataset."
else:
    header = rows[0]
    data_rows = rows[1:] if len(rows) > 1 else []
    numeric_values = []
    for row in data_rows:
        for value in row:
            try:
                numeric_values.append(float(value))
            except ValueError:
                pass

    numeric_mean_text = "n/a"
    if numeric_values:
        numeric_mean_text = format(sum(numeric_values) / len(numeric_values), ".4f")

    result = (
        "Rows: " + str(len(data_rows)) + "\\n"
        + "Columns: " + str(len(header)) + "\\n"
        + "Numeric cells: " + str(len(numeric_values)) + "\\n"
        + "Numeric mean: " + numeric_mean_text
    )
""".strip()
