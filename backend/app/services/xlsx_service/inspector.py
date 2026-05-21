from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import asdict
from pathlib import PurePosixPath
from typing import Any

from backend.app.services.xlsx_service.models import (
    XLSX_INSPECT_SCHEMA_VERSION,
    XlsxFormulaRecord,
    XlsxInspectArtifactBundle,
    XlsxInspectResult,
    XlsxSheetInspection,
)

_CELL_RE = re.compile(r"^([A-Z]+)([0-9]+)$")


class XlsxInspectionError(ValueError):
    """Raised when an XLSX/CSV payload cannot be inspected honestly."""


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _tag_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _column_index(cell_ref: str) -> int:
    match = _CELL_RE.match(cell_ref.upper())
    if not match:
        return 0
    letters = match.group(1)
    value = 0
    for letter in letters:
        value = value * 26 + (ord(letter) - ord("A") + 1)
    return value


def _row_index(cell_ref: str) -> int:
    match = _CELL_RE.match(cell_ref.upper())
    return int(match.group(2)) if match else 0


def _column_name(index: int) -> str:
    if index <= 0:
        return "A"
    letters: list[str] = []
    value = index
    while value:
        value, remainder = divmod(value - 1, 26)
        letters.append(chr(ord("A") + remainder))
    return "".join(reversed(letters))


def _used_range(max_row: int, max_column: int) -> str:
    if max_row <= 0 or max_column <= 0:
        return "A1:A1"
    return f"A1:{_column_name(max_column)}{max_row}"


def _safe_sheet_slug(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    return slug.strip("._-") or "sheet"


def _csv_bytes(rows: list[list[str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _json_bytes(payload: dict[str, Any] | list[Any]) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _relationship_targets(workbook_rels: bytes) -> dict[str, str]:
    root = ET.fromstring(workbook_rels)
    mapping: dict[str, str] = {}
    for node in root:
        if _tag_name(node) != "Relationship":
            continue
        rel_id = node.attrib.get("Id")
        target = node.attrib.get("Target")
        if rel_id and target:
            mapping[rel_id] = target
    return mapping


def _workbook_sheets(workbook_xml: bytes) -> list[tuple[str, str | None]]:
    root = ET.fromstring(workbook_xml)
    sheets: list[tuple[str, str | None]] = []
    for node in root.iter():
        if _tag_name(node) != "sheet":
            continue
        name = node.attrib.get("name") or f"Sheet{len(sheets) + 1}"
        rel_id = None
        for attr_name, attr_value in node.attrib.items():
            if attr_name.endswith("}id") or attr_name == "r:id":
                rel_id = attr_value
                break
        sheets.append((name, rel_id))
    return sheets


def _shared_strings(workbook_zip: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in workbook_zip.namelist():
        return []
    root = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for si in root:
        if _tag_name(si) != "si":
            continue
        parts: list[str] = []
        for text_node in si.iter():
            if _tag_name(text_node) == "t" and text_node.text:
                parts.append(text_node.text)
        values.append("".join(parts))
    return values


def _cell_text(cell: ET.Element, shared_strings: list[str]) -> tuple[str, str | None]:
    cell_type = cell.attrib.get("t")
    formula_text: str | None = None
    value_text = ""
    inline_parts: list[str] = []

    for child in cell:
        tag = _tag_name(child)
        if tag == "f":
            formula_text = child.text or ""
        elif tag == "v":
            value_text = child.text or ""
        elif tag == "is":
            for text_node in child.iter():
                if _tag_name(text_node) == "t" and text_node.text:
                    inline_parts.append(text_node.text)

    if inline_parts:
        value_text = "".join(inline_parts)
    elif cell_type == "s" and value_text.isdigit():
        index = int(value_text)
        if 0 <= index < len(shared_strings):
            value_text = shared_strings[index]

    if formula_text:
        return f"={formula_text}", formula_text
    return value_text, formula_text


def _worksheet_path_for(rel_target: str | None, fallback_index: int) -> str:
    if rel_target:
        rel_path = PurePosixPath(rel_target)
        if not rel_path.is_absolute():
            return str(PurePosixPath("xl") / rel_path)
        return str(rel_path).lstrip("/")
    return f"xl/worksheets/sheet{fallback_index}.xml"


def _inspect_worksheet(
    *,
    workbook_zip: zipfile.ZipFile,
    worksheet_file: str,
    sheet_name: str,
    shared_strings: list[str],
) -> tuple[XlsxSheetInspection, tuple[XlsxFormulaRecord, ...], bytes]:
    root = ET.fromstring(workbook_zip.read(worksheet_file))
    dimension_ref: str | None = None
    rows_by_index: dict[int, dict[int, str]] = {}
    formulas: list[XlsxFormulaRecord] = []
    non_empty_cells = 0
    table_like_rows = 0
    max_row = 0
    max_column = 0

    for node in root.iter():
        if _tag_name(node) == "dimension":
            dimension_ref = node.attrib.get("ref")
            break

    for row_node in root.iter():
        if _tag_name(row_node) != "row":
            continue
        row_cells: dict[int, str] = {}
        row_index = int(row_node.attrib.get("r", "0") or 0)
        for cell in row_node:
            if _tag_name(cell) != "c":
                continue
            cell_ref = cell.attrib.get("r", "")
            col_index = _column_index(cell_ref) or (len(row_cells) + 1)
            row_index = row_index or _row_index(cell_ref)
            value, formula = _cell_text(cell, shared_strings)
            if value != "" or formula is not None:
                row_cells[col_index] = value
                non_empty_cells += 1
                max_row = max(max_row, row_index)
                max_column = max(max_column, col_index)
                if formula is not None:
                    formulas.append(
                        XlsxFormulaRecord(
                            sheet_name=sheet_name,
                            cell_ref=cell_ref or f"{_column_name(col_index)}{row_index}",
                            formula=formula,
                            worksheet_file=worksheet_file,
                        )
                    )
        if row_cells:
            rows_by_index[row_index] = row_cells
            if len([value for value in row_cells.values() if value != ""]) >= 2:
                table_like_rows += 1

    preview_rows: list[list[str]] = []
    for row_number in range(1, max_row + 1):
        row_values = rows_by_index.get(row_number, {})
        preview_rows.append([row_values.get(column_number, "") for column_number in range(1, max_column + 1)])

    preview_name = f"table_previews/{_safe_sheet_slug(sheet_name)}.csv"
    sheet = XlsxSheetInspection(
        sheet_name=sheet_name,
        worksheet_file=worksheet_file,
        dimension_ref=dimension_ref,
        used_range=dimension_ref or _used_range(max_row, max_column),
        max_row=max_row,
        max_column=max_column,
        non_empty_cell_count=non_empty_cells,
        formula_count=len(formulas),
        table_like_row_count=table_like_rows,
        preview_artifact=preview_name,
    )
    return sheet, tuple(formulas), _csv_bytes(preview_rows)


def inspect_xlsx_content(content: bytes, *, source_filename: str = "workbook.xlsx") -> XlsxInspectResult:
    errors: list[str] = []
    sheets: list[XlsxSheetInspection] = []
    formulas: list[XlsxFormulaRecord] = []
    source_hash = _sha256(content)

    try:
        with zipfile.ZipFile(io.BytesIO(content), "r") as workbook_zip:
            names = set(workbook_zip.namelist())
            required = {"[Content_Types].xml", "xl/workbook.xml"}
            missing = sorted(required - names)
            if missing:
                raise XlsxInspectionError(f"missing required XLSX package files: {', '.join(missing)}")

            workbook_xml = workbook_zip.read("xl/workbook.xml")
            rels = {}
            if "xl/_rels/workbook.xml.rels" in names:
                rels = _relationship_targets(workbook_zip.read("xl/_rels/workbook.xml.rels"))
            workbook_sheets = _workbook_sheets(workbook_xml)
            shared_strings = _shared_strings(workbook_zip)

            for index, (sheet_name, rel_id) in enumerate(workbook_sheets, start=1):
                worksheet_file = _worksheet_path_for(rels.get(rel_id or ""), index)
                if worksheet_file not in names:
                    raise XlsxInspectionError(f"worksheet missing for sheet {sheet_name!r}: {worksheet_file}")
                sheet, sheet_formulas, _preview = _inspect_worksheet(
                    workbook_zip=workbook_zip,
                    worksheet_file=worksheet_file,
                    sheet_name=sheet_name,
                    shared_strings=shared_strings,
                )
                sheets.append(sheet)
                formulas.extend(sheet_formulas)
    except (zipfile.BadZipFile, ET.ParseError, KeyError, XlsxInspectionError) as exc:
        errors.append(str(exc))

    non_empty = sum(sheet.non_empty_cell_count for sheet in sheets)
    table_like = sum(sheet.table_like_row_count for sheet in sheets)
    status = "ready" if not errors and sheets and non_empty > 0 else "failed"
    return XlsxInspectResult(
        schema_version=XLSX_INSPECT_SCHEMA_VERSION,
        source_filename=source_filename,
        source_kind="xlsx",
        status=status,
        workbook_opens=status == "ready",
        sheet_count=len(sheets),
        sheets=tuple(sheets),
        formulas=tuple(formulas),
        non_empty_cell_count=non_empty,
        formula_count=len(formulas),
        table_like_row_count=table_like,
        destructive_edit_performed=False,
        source_sha256=source_hash,
        errors=tuple(errors),
    )


def inspect_csv_content(content: bytes, *, source_filename: str = "workbook.csv") -> XlsxInspectResult:
    source_hash = _sha256(content)
    errors: list[str] = []
    rows: list[list[str]] = []
    try:
        text = content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))
    except UnicodeDecodeError as exc:
        errors.append(f"invalid CSV encoding: {exc}")

    max_column = max((len(row) for row in rows), default=0)
    non_empty = sum(1 for row in rows for value in row if value != "")
    table_like = sum(1 for row in rows if len([value for value in row if value != ""]) >= 2)
    status = "ready" if not errors and non_empty > 0 else "failed"
    sheet = XlsxSheetInspection(
        sheet_name=PurePosixPath(source_filename).stem or "CSV",
        worksheet_file=source_filename,
        dimension_ref=None,
        used_range=_used_range(len(rows), max_column),
        max_row=len(rows),
        max_column=max_column,
        non_empty_cell_count=non_empty,
        formula_count=0,
        table_like_row_count=table_like,
        preview_artifact="table_previews/csv_input.csv",
    )
    return XlsxInspectResult(
        schema_version=XLSX_INSPECT_SCHEMA_VERSION,
        source_filename=source_filename,
        source_kind="csv",
        status=status,
        workbook_opens=status == "ready",
        sheet_count=1 if status == "ready" else 0,
        sheets=(sheet,) if status == "ready" else (),
        formulas=(),
        non_empty_cell_count=non_empty,
        formula_count=0,
        table_like_row_count=table_like,
        destructive_edit_performed=False,
        source_sha256=source_hash,
        errors=tuple(errors),
    )


def inspect_tabular_content(content: bytes, *, source_filename: str) -> XlsxInspectResult:
    suffix = PurePosixPath(source_filename).suffix.lower()
    if suffix == ".csv":
        return inspect_csv_content(content, source_filename=source_filename)
    return inspect_xlsx_content(content, source_filename=source_filename)


def _bundle_common(result: XlsxInspectResult, source_content: bytes) -> dict[str, bytes]:
    formula_inventory = {
        "schema_version": result.schema_version,
        "source_filename": result.source_filename,
        "formula_count": result.formula_count,
        "formulas": [formula.as_dict() for formula in result.formulas],
    }
    workbook_manifest = {
        "schema_version": result.schema_version,
        "source_filename": result.source_filename,
        "source_kind": result.source_kind,
        "source_sha256": result.source_sha256,
        "sheet_count": result.sheet_count,
        "sheets": [sheet.as_dict() for sheet in result.sheets],
        "destructive_edit_performed": result.destructive_edit_performed,
    }
    evidence_manifest = {
        "schema_version": result.schema_version,
        "source_filename": result.source_filename,
        "source_sha256": result.source_sha256,
        "evidence_items": [
            {
                "evidence_id": f"sheet:{sheet.sheet_name}",
                "source_range": sheet.used_range,
                "preview_artifact": sheet.preview_artifact,
                "worksheet_file": sheet.worksheet_file,
            }
            for sheet in result.sheets
        ],
    }
    quality_report = {
        "schema_version": result.schema_version,
        "status": result.status,
        "checks": {
            "workbook_opens": result.workbook_opens,
            "sheet_metadata_extracted": result.sheet_count > 0,
            "formula_inventory_written": True,
            "table_previews_written": all(sheet.preview_artifact for sheet in result.sheets),
            "destructive_edit_performed": result.destructive_edit_performed,
            "source_hash_recorded": bool(result.source_sha256),
        },
        "errors": list(result.errors),
    }
    artifacts: dict[str, bytes] = {
        "workbook.xlsx" if result.source_kind == "xlsx" else "workbook.csv": source_content,
        "workbook_manifest.json": _json_bytes(workbook_manifest),
        "xlsx_analysis_report.json": _json_bytes(result.as_dict()),
        "formula_inventory.json": _json_bytes(formula_inventory),
        "source_evidence_manifest.json": _json_bytes(evidence_manifest),
        "quality_report.json": _json_bytes(quality_report),
    }
    return artifacts


def build_xlsx_inspect_artifact_bundle(content: bytes, *, source_filename: str = "workbook.xlsx") -> XlsxInspectArtifactBundle:
    result = inspect_tabular_content(content, source_filename=source_filename)
    artifacts = _bundle_common(result, content)
    if result.status == "ready":
        if result.source_kind == "csv":
            artifacts["table_previews/csv_input.csv"] = content
        else:
            with zipfile.ZipFile(io.BytesIO(content), "r") as workbook_zip:
                shared = _shared_strings(workbook_zip)
                rels = _relationship_targets(workbook_zip.read("xl/_rels/workbook.xml.rels")) if "xl/_rels/workbook.xml.rels" in workbook_zip.namelist() else {}
                for index, (sheet_name, rel_id) in enumerate(_workbook_sheets(workbook_zip.read("xl/workbook.xml")), start=1):
                    worksheet_file = _worksheet_path_for(rels.get(rel_id or ""), index)
                    sheet, _formulas, preview = _inspect_worksheet(
                        workbook_zip=workbook_zip,
                        worksheet_file=worksheet_file,
                        sheet_name=sheet_name,
                        shared_strings=shared,
                    )
                    artifacts[sheet.preview_artifact] = preview
    artifact_entries = [
        {
            "path": name,
            "size_bytes": len(payload),
            "sha256": _sha256(payload),
        }
        for name, payload in sorted(artifacts.items())
    ]
    artifact_entries.append(
        {
            "path": "artifact_manifest.json",
            "size_bytes": None,
            "sha256": None,
            "self_reference": True,
        }
    )
    artifact_manifest = {
        "schema_version": result.schema_version,
        "workflow_id": "xlsx",
        "status": result.status,
        "artifacts": artifact_entries,
    }
    artifacts["artifact_manifest.json"] = _json_bytes(artifact_manifest)
    return XlsxInspectArtifactBundle(result=result, artifacts=artifacts)


def write_xlsx_inspect_artifact_bundle(bundle: XlsxInspectArtifactBundle, output_dir: str | PurePosixPath) -> list[str]:
    from pathlib import Path

    root = Path(output_dir)
    written: list[str] = []
    for name, payload in bundle.artifacts.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        written.append(name)
    return sorted(written)


def sample_xlsx_bytes() -> bytes:
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Revenue" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""
    relationships = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
    sheet = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <dimension ref="A1:B4"/>
  <sheetData>
    <row r="1"><c r="A1" t="inlineStr"><is><t>Metric</t></is></c><c r="B1" t="inlineStr"><is><t>Value</t></is></c></row>
    <row r="2"><c r="A2" t="inlineStr"><is><t>Revenue Q1</t></is></c><c r="B2"><v>100</v></c></row>
    <row r="3"><c r="A3" t="inlineStr"><is><t>Revenue Q2</t></is></c><c r="B3"><v>200</v></c></row>
    <row r="4"><c r="A4" t="inlineStr"><is><t>Total</t></is></c><c r="B4"><f>SUM(B2:B3)</f><v>300</v></c></row>
  </sheetData>
</worksheet>"""
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as xlsx:
        xlsx.writestr("[Content_Types].xml", "<Types/>")
        xlsx.writestr("_rels/.rels", "<Relationships/>")
        xlsx.writestr("xl/workbook.xml", workbook)
        xlsx.writestr("xl/_rels/workbook.xml.rels", relationships)
        xlsx.writestr("xl/worksheets/sheet1.xml", sheet)
    return payload.getvalue()
