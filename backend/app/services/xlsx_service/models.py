from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


XLSX_INSPECT_SCHEMA_VERSION = "kr5a.xlsx_inspect.v1"


@dataclass(frozen=True)
class XlsxFormulaRecord:
    sheet_name: str
    cell_ref: str
    formula: str
    worksheet_file: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class XlsxSheetInspection:
    sheet_name: str
    worksheet_file: str
    dimension_ref: str | None
    used_range: str
    max_row: int
    max_column: int
    non_empty_cell_count: int
    formula_count: int
    table_like_row_count: int
    preview_artifact: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class XlsxInspectResult:
    schema_version: str
    source_filename: str
    source_kind: str
    status: str
    workbook_opens: bool
    sheet_count: int
    sheets: tuple[XlsxSheetInspection, ...]
    formulas: tuple[XlsxFormulaRecord, ...]
    non_empty_cell_count: int
    formula_count: int
    table_like_row_count: int
    destructive_edit_performed: bool
    source_sha256: str
    errors: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sheets"] = [sheet.as_dict() for sheet in self.sheets]
        payload["formulas"] = [formula.as_dict() for formula in self.formulas]
        return payload


@dataclass(frozen=True)
class XlsxInspectArtifactBundle:
    result: XlsxInspectResult
    artifacts: dict[str, bytes]

    def artifact_names(self) -> tuple[str, ...]:
        return tuple(sorted(self.artifacts))

    def text_artifact(self, name: str) -> str:
        return self.artifacts[name].decode("utf-8")
