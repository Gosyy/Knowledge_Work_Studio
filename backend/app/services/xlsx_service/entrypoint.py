from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.app.services.xlsx_service.models import XlsxInspectResult
from backend.app.services.xlsx_service.service import XlsxService


@dataclass(frozen=True)
class XlsxInspectRequest:
    content: bytes
    source_filename: str = "workbook.xlsx"


@dataclass(frozen=True)
class XlsxInspectResultPayload:
    status: str
    workbook_opens: bool
    sheet_count: int
    formula_count: int
    table_like_row_count: int
    artifact_names: tuple[str, ...]
    analysis_report: dict[str, object]


@dataclass
class XlsxServiceEntrypoint:
    service: XlsxService

    def inspect(self, request: XlsxInspectRequest) -> XlsxInspectResultPayload:
        bundle = self.service.build_artifact_bundle(
            request.content,
            source_filename=request.source_filename,
        )
        result: XlsxInspectResult = bundle.result
        return XlsxInspectResultPayload(
            status=result.status,
            workbook_opens=result.workbook_opens,
            sheet_count=result.sheet_count,
            formula_count=result.formula_count,
            table_like_row_count=result.table_like_row_count,
            artifact_names=bundle.artifact_names(),
            analysis_report=result.as_dict(),
        )

    def write_bundle(self, request: XlsxInspectRequest, *, output_dir: Path) -> list[str]:
        return self.service.write_artifact_bundle(
            request.content,
            output_dir=output_dir,
            source_filename=request.source_filename,
        )
