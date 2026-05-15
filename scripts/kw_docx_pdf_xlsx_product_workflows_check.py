#!/usr/bin/env python3
"""KR-2F DOCX/PDF/XLSX product workflow coverage check.

This checker is intentionally product-named and additive. DOCX/PDF use the
existing runtime services; XLSX gets a portable stdlib OOXML inspector as the
first product contract until a dedicated XLSX service is introduced.
"""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.docx_service import DocxIngestionError, DocxService
from backend.app.services.pdf_service import PdfImageOnlyError, PdfService


PRODUCT_DOCS: tuple[str, ...] = (
    "docs/workflows/DOCX_WORKFLOW.md",
    "docs/workflows/PDF_WORKFLOW.md",
    "docs/workflows/XLSX_WORKFLOW.md",
    "docs/quality/XLSX_VALIDATION.md",
)

PRODUCT_TESTS: tuple[str, ...] = (
    "backend/tests/workflows/test_docx_workflow_product_contract.py",
    "backend/tests/workflows/test_pdf_workflow_product_contract.py",
    "backend/tests/workflows/test_xlsx_workflow_product_contract.py",
    "backend/tests/quality/test_xlsx_validation_product_contract.py",
    "backend/tests/smoke/test_docx_pdf_xlsx_product_workflows.py",
)

LEGACY_SAFETY_NETS: tuple[str, ...] = (
    "backend/tests/smoke/test_rf3_docx_pdf_real_ingestion.py",
    "scripts/kw_docx_pdf_real_ingestion_check.py",
)

FORBIDDEN_POSITIVE_CLAIMS: tuple[str, ...] = (
    "xlsx workflow complete",
    "excel parity achieved",
    "full excel parity",
    "kimi-level achieved",
    "selected workflow parity achieved",
)


@dataclass(frozen=True)
class FileStatus:
    path: str
    exists: bool
    status: str
    reason: str


@dataclass(frozen=True)
class XlsxInspection:
    status: str
    sheet_count: int
    sheet_names: tuple[str, ...]
    worksheet_files: tuple[str, ...]
    non_empty_cell_count: int
    formula_count: int
    formula_refs: tuple[str, ...]
    table_like_row_count: int
    workbook_opens: bool
    destructive_edit_performed: bool
    errors: tuple[str, ...]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sample_docx_bytes() -> bytes:
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Product DOCX workflow extracts paragraph text.</w:t></w:r></w:p>
    <w:p><w:r><w:t>Product DOCX workflow preserves table signals.</w:t></w:r></w:p>
    <w:tbl><w:tr><w:tc><w:p><w:r><w:t>DOCX table cell evidence.</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
  </w:body>
</w:document>"""
    payload = BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", "<Types/>")
        docx.writestr("_rels/.rels", "<Relationships/>")
        docx.writestr("word/document.xml", document_xml)
    return payload.getvalue()


def sample_pdf_bytes() -> bytes:
    return b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /Contents 4 0 R >> endobj
4 0 obj << /Length 150 >> stream
BT /F1 12 Tf 72 720 Td (Product PDF workflow extracts text layer.) Tj 0 -18 Td (Second PDF sentence remains available.) Tj ET
endstream endobj
%%EOF
"""


def image_only_pdf_bytes() -> bytes:
    return b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /Resources << /XObject << /Im1 4 0 R >> >> >> endobj
4 0 obj << /Type /XObject /Subtype /Image /Width 10 /Height 10 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length 3 >> stream
abc
endstream endobj
%%EOF
"""


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
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr"><is><t>Metric</t></is></c>
      <c r="B1" t="inlineStr"><is><t>Value</t></is></c>
    </row>
    <row r="2">
      <c r="A2" t="inlineStr"><is><t>Revenue Q1</t></is></c>
      <c r="B2"><v>100</v></c>
    </row>
    <row r="3">
      <c r="A3" t="inlineStr"><is><t>Revenue Q2</t></is></c>
      <c r="B3"><v>200</v></c>
    </row>
    <row r="4">
      <c r="A4" t="inlineStr"><is><t>Total</t></is></c>
      <c r="B4"><f>SUM(B2:B3)</f><v>300</v></c>
    </row>
  </sheetData>
</worksheet>"""
    payload = BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as xlsx:
        xlsx.writestr("[Content_Types].xml", "<Types/>")
        xlsx.writestr("_rels/.rels", "<Relationships/>")
        xlsx.writestr("xl/workbook.xml", workbook)
        xlsx.writestr("xl/_rels/workbook.xml.rels", relationships)
        xlsx.writestr("xl/worksheets/sheet1.xml", sheet)
    return payload.getvalue()


def _xml_root(payload: bytes) -> ET.Element:
    return ET.fromstring(payload)


def _tag_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def inspect_xlsx_bytes(content: bytes) -> XlsxInspection:
    errors: list[str] = []
    sheet_names: list[str] = []
    worksheet_files: list[str] = []
    non_empty_cells = 0
    formula_refs: list[str] = []
    table_like_rows = 0

    try:
        with zipfile.ZipFile(BytesIO(content), "r") as workbook_zip:
            names = set(workbook_zip.namelist())
            required = {"[Content_Types].xml", "xl/workbook.xml"}
            missing = sorted(required - names)
            if missing:
                errors.append(f"missing required XLSX package files: {', '.join(missing)}")

            workbook_xml = workbook_zip.read("xl/workbook.xml")
            workbook_root = _xml_root(workbook_xml)
            for node in workbook_root.iter():
                if _tag_name(node) == "sheet":
                    name = node.attrib.get("name")
                    if name:
                        sheet_names.append(name)

            worksheet_files = sorted(name for name in names if name.startswith("xl/worksheets/") and name.endswith(".xml"))
            if not worksheet_files:
                errors.append("no worksheet XML files found")

            for worksheet_name in worksheet_files:
                root = _xml_root(workbook_zip.read(worksheet_name))
                for row in root.iter():
                    if _tag_name(row) != "row":
                        continue
                    row_non_empty = 0
                    for cell in row:
                        if _tag_name(cell) != "c":
                            continue
                        has_value = any(_tag_name(child) in {"v", "is", "f"} for child in cell)
                        if has_value:
                            row_non_empty += 1
                            non_empty_cells += 1
                        for child in cell:
                            if _tag_name(child) == "f":
                                ref = cell.attrib.get("r", "")
                                formula_refs.append(ref or "<unknown>")
                    if row_non_empty >= 2:
                        table_like_rows += 1
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        errors.append(f"invalid XLSX package: {exc}")

    status = "ready" if not errors and non_empty_cells > 0 else "failed"
    return XlsxInspection(
        status=status,
        sheet_count=len(sheet_names) if sheet_names else len(worksheet_files),
        sheet_names=tuple(sheet_names),
        worksheet_files=tuple(worksheet_files),
        non_empty_cell_count=non_empty_cells,
        formula_count=len(formula_refs),
        formula_refs=tuple(formula_refs),
        table_like_row_count=table_like_rows,
        workbook_opens=not errors,
        destructive_edit_performed=False,
        errors=tuple(errors),
    )


def file_status(repo_root: Path, path: str, *, role: str) -> FileStatus:
    exists = (repo_root / path).exists()
    return FileStatus(path=path, exists=exists, status="ready" if exists else "missing", reason=f"{role} {'exists' if exists else 'is missing'}")


def scan_positive_claims(repo_root: Path) -> list[str]:
    issues: list[str] = []
    for rel_path in PRODUCT_DOCS + PRODUCT_TESTS:
        path = repo_root / rel_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for claim in FORBIDDEN_POSITIVE_CLAIMS:
            if claim in text:
                issues.append(f"{rel_path}: contains unsupported positive claim {claim!r}")
    return issues


def check_docs_codex_not_moved(repo_root: Path) -> list[str]:
    codex = repo_root / "docs" / "codex"
    if not codex.exists():
        return ["docs/codex is missing; physical archive remains blocked until stage checkers/tests are rewritten"]
    if not any(codex.glob("*.md")):
        return ["docs/codex has no markdown files; physical archive appears to have happened too early"]
    return []


def build_report(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()

    product_statuses = [file_status(repo_root, path, role="DOCX/PDF/XLSX product test") for path in PRODUCT_TESTS]
    doc_statuses = [file_status(repo_root, path, role="DOCX/PDF/XLSX product doc") for path in PRODUCT_DOCS]
    legacy_statuses = [file_status(repo_root, path, role="legacy RF safety net") for path in LEGACY_SAFETY_NETS]

    issues: list[str] = []
    for status in product_statuses + doc_statuses:
        if not status.exists:
            issues.append(f"required file missing: {status.path}")

    try:
        docx = DocxService().ingest_docx(sample_docx_bytes(), source_filename="product.docx")
        if "Product DOCX workflow extracts paragraph text." not in docx.extracted_text:
            issues.append("DOCX service did not extract expected product sample text")
    except (DocxIngestionError, Exception) as exc:
        issues.append(f"DOCX product sample failed: {exc}")

    try:
        pdf = PdfService().ingest_pdf(sample_pdf_bytes(), source_filename="product.pdf", max_sentences=1)
        if "Product PDF workflow extracts text layer." not in pdf.extracted_text:
            issues.append("PDF service did not extract expected product sample text")
    except Exception as exc:
        issues.append(f"PDF product sample failed: {exc}")

    xlsx = inspect_xlsx_bytes(sample_xlsx_bytes())
    if xlsx.status != "ready":
        issues.append(f"XLSX product sample failed: {xlsx.errors}")
    if xlsx.formula_count < 1:
        issues.append("XLSX product sample did not report formulas")

    issues.extend(scan_positive_claims(repo_root))
    issues.extend(check_docs_codex_not_moved(repo_root))

    warnings = [f"legacy safety net missing or already retired: {status.path}" for status in legacy_statuses if not status.exists]

    return {
        "generated_at": utc_now(),
        "status": "ready" if not issues else "needs_work",
        "purpose": "KR-2F first-class DOCX/PDF/XLSX product workflow tests; no legacy RF tests are removed.",
        "summary": {
            "product_tests_required": len(PRODUCT_TESTS),
            "product_tests_ready": sum(1 for status in product_statuses if status.exists),
            "product_docs_checked": len(PRODUCT_DOCS),
            "product_docs_ready": sum(1 for status in doc_statuses if status.exists),
            "legacy_safety_net_files_checked": len(LEGACY_SAFETY_NETS),
            "xlsx_formula_inventory_supported": xlsx.formula_count > 0,
            "xlsx_workbook_opens": xlsx.workbook_opens,
            "physical_docs_codex_archive_allowed": False,
            "physical_docs_codex_archive_blocked_until": "direct docs/codex dependencies in stage checkers/tests are rewritten or archived",
        },
        "docx_pdf_xlsx_product_test_statuses": [asdict(status) for status in product_statuses],
        "product_doc_statuses": [asdict(status) for status in doc_statuses],
        "legacy_safety_net_statuses": [asdict(status) for status in legacy_statuses],
        "xlsx_sample_inspection": asdict(xlsx),
        "issues": issues,
        "warnings": warnings,
        "next_steps": [
            "KR-3A/KR-3B: harden path portability after product workflow replacement coverage exists.",
            "KR-4A: introduce shared workflow contract types for DOCX/PDF/XLSX/Slides/Python/Browser.",
            "KR-5A: implement a dedicated XLSX inspect workflow/service based on this portable contract.",
        ],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# KR-2F DOCX/PDF/XLSX Product Workflow Coverage",
        "",
        "KR-2F adds first-class product-level tests for DOCX, PDF, and XLSX/Excel workflows.",
        "It is additive only: legacy RF tests and `docs/codex` remain in place.",
        "",
        "## Summary",
        "",
        f"- Status: `{report['status']}`",
        f"- Product tests ready: `{summary['product_tests_ready']}` / `{summary['product_tests_required']}`",
        f"- Product docs ready: `{summary['product_docs_ready']}` / `{summary['product_docs_checked']}`",
        f"- XLSX workbook opens: `{summary['xlsx_workbook_opens']}`",
        f"- XLSX formula inventory supported: `{summary['xlsx_formula_inventory_supported']}`",
        f"- Physical `docs/codex` archive allowed: `{summary['physical_docs_codex_archive_allowed']}`",
        "",
        "## Product tests",
        "",
    ]
    for status in report["docx_pdf_xlsx_product_test_statuses"]:
        lines.append(f"- `{status['path']}` — `{status['status']}`")
    lines += ["", "## XLSX sample inspection", ""]
    xlsx = report["xlsx_sample_inspection"]
    lines.append(f"- Status: `{xlsx['status']}`")
    lines.append(f"- Sheet count: `{xlsx['sheet_count']}`")
    lines.append(f"- Formula count: `{xlsx['formula_count']}`")
    lines.append(f"- Non-empty cells: `{xlsx['non_empty_cell_count']}`")
    lines += ["", "## Issues", ""]
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"- {issue}")
    else:
        lines.append("- None")
    lines += ["", "## Warnings", ""]
    if report["warnings"]:
        for warning in report["warnings"]:
            lines.append(f"- {warning}")
    else:
        lines.append("- None")
    lines += ["", "## Next steps", ""]
    for step in report["next_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def write_zip(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description="Check KR-2F DOCX/PDF/XLSX product workflow coverage.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, default=None)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_report(args.repo_root)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "kr2f_docx_pdf_xlsx_product_workflows.json", report)
    (output_dir / "kr2f_docx_pdf_xlsx_product_workflows.md").write_text(render_markdown(report), encoding="utf-8")

    if args.zip_out:
        write_zip(output_dir, args.zip_out.resolve())

    if args.json:
        print(json.dumps({"status": report["status"], **report["summary"]}, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KR-2F DOCX/PDF/XLSX product workflows: {report['status']}")
        print(f"Report written to: {output_dir}")

    if args.require_ready and report["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
