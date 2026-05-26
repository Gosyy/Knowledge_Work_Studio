from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import posixpath
import re
from dataclasses import asdict, dataclass, field
from io import BytesIO, StringIO
from typing import Any, Literal
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

SOURCE_INGESTION_SCHEMA_VERSION = "offline_source_ingestion.v1"
SOURCE_ASSET_REGISTRY_SCHEMA_VERSION = "source_asset_registry.v1"
SOURCE_STRUCTURE_SCHEMA_VERSION = "source_structure.v1"
SOURCE_EXTRACTION_FIDELITY_SCHEMA_VERSION = "source_extraction_fidelity.v1"

SourceIngestionStatus = Literal["ready", "unsupported", "failed"]
SourceKind = Literal["text", "markdown", "csv", "json", "yaml", "docx", "pdf", "xlsx", "pptx", "unknown"]

_TEXT_FILE_TYPES = {"txt", "text", "log"}
_MARKDOWN_FILE_TYPES = {"md", "markdown"}
_CSV_FILE_TYPES = {"csv"}
_JSON_FILE_TYPES = {"json"}
_YAML_FILE_TYPES = {"yaml", "yml"}
_DOCX_FILE_TYPES = {"docx"}
_PDF_FILE_TYPES = {"pdf"}
_XLSX_FILE_TYPES = {"xlsx", "xlsm"}
_PPTX_FILE_TYPES = {"pptx"}

_WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
_DRAWING_NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
_PRESENTATION_NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
_SPREADSHEET_NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_CHART_NS = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}
_OFFICE_REL_NS = {"r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
_REL_NS = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}


@dataclass(frozen=True)
class SourceIngestionFragment:
    fragment_id: str
    source_id: str
    kind: str
    text: str
    provenance_ref: str
    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    heading_level: int | None = None
    role: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceTableCandidate:
    table_id: str
    source_id: str
    rows: list[list[str]]
    provenance_ref: str
    caption: str | None = None
    sheet_name: str | None = None
    page_number: int | None = None
    slide_number: int | None = None
    has_formula: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceStructureElement:
    element_id: str
    source_id: str
    element_type: str
    provenance_ref: str
    text: str | None = None
    role: str | None = None
    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    coordinates: dict[str, float] | None = None
    style: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceChartDataCandidate:
    candidate_id: str
    source_id: str
    chart_type: str
    provenance_ref: str
    data_refs: list[str] = field(default_factory=list)
    title: str | None = None
    sheet_name: str | None = None
    slide_number: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceAsset:
    asset_id: str
    source_id: str
    asset_type: str
    path: str
    provenance_ref: str
    checksum_sha256: str
    size_bytes: int
    mime_type: str | None = None
    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    width_px: int | None = None
    height_px: int | None = None
    content_bytes: bytes | None = field(default=None, repr=False, compare=False)
    relationship_id: str | None = None
    owner_part: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("content_bytes", None)
        return payload


@dataclass(frozen=True)
class SourceIngestionReport:
    schema_version: str
    source_id: str
    source_kind: SourceKind
    status: SourceIngestionStatus
    title: str | None
    fragments: list[SourceIngestionFragment] = field(default_factory=list)
    tables: list[SourceTableCandidate] = field(default_factory=list)
    assets: list[SourceAsset] = field(default_factory=list)
    structures: list[SourceStructureElement] = field(default_factory=list)
    chart_candidates: list[SourceChartDataCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    provenance_manifest: dict[str, Any] = field(default_factory=dict)
    source_asset_registry: dict[str, Any] = field(default_factory=dict)
    extraction_fidelity: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["fragments"] = [fragment.as_dict() for fragment in self.fragments]
        payload["tables"] = [table.as_dict() for table in self.tables]
        payload["assets"] = [asset.as_dict() for asset in self.assets]
        payload["structures"] = [structure.as_dict() for structure in self.structures]
        payload["chart_candidates"] = [candidate.as_dict() for candidate in self.chart_candidates]
        return payload


class OfflineSourceIngestionEngine:
    """Deterministic offline source ingestion engine for KR-7D.1.

    The engine is intentionally local-only and does not use network calls, LLMs,
    OCR, generated images, or hidden embedding services. Unsupported extraction
    is reported as unsupported instead of being faked.
    """

    def ingest_bytes(
        self,
        raw_content: bytes,
        *,
        source_id: str,
        file_type: str = "",
        mime_type: str = "",
        title: str | None = None,
    ) -> SourceIngestionReport:
        source_kind = detect_source_kind(file_type=file_type, mime_type=mime_type, title=title)
        try:
            if source_kind in {"text", "markdown", "csv", "json", "yaml"}:
                report = self._ingest_text_like(
                    raw_content,
                    source_id=source_id,
                    source_kind=source_kind,
                    title=title,
                )
            elif source_kind == "docx":
                report = self._ingest_docx(raw_content, source_id=source_id, title=title)
            elif source_kind == "pptx":
                report = self._ingest_pptx(raw_content, source_id=source_id, title=title)
            elif source_kind == "xlsx":
                report = self._ingest_xlsx(raw_content, source_id=source_id, title=title)
            elif source_kind == "pdf":
                report = self._ingest_pdf(raw_content, source_id=source_id, title=title)
            else:
                return _unsupported_report(
                    source_id=source_id,
                    source_kind="unknown",
                    title=title,
                    warning="Unsupported source type; KR-7D.1 does not guess binary formats.",
                )
        except Exception as exc:  # pragma: no cover - defensive fail-closed path
            return _failed_report(source_id=source_id, source_kind=source_kind, title=title, error=str(exc))
        return _with_manifests(report)

    def _ingest_text_like(
        self,
        raw_content: bytes,
        *,
        source_id: str,
        source_kind: SourceKind,
        title: str | None,
    ) -> SourceIngestionReport:
        text = _decode_utf8(raw_content)
        fragments: list[SourceIngestionFragment] = []
        tables: list[SourceTableCandidate] = []
        structures: list[SourceStructureElement] = []
        chart_candidates: list[SourceChartDataCandidate] = []

        if source_kind == "markdown":
            fragments.extend(_markdown_fragments(text, source_id=source_id))
            tables.extend(_markdown_tables(text, source_id=source_id))
            structures.extend(_markdown_structures(text, source_id=source_id, tables=tables))
        elif source_kind == "csv":
            rows = _csv_rows(text)
            tables.append(
                SourceTableCandidate(
                    table_id=f"{source_id}_table_001",
                    source_id=source_id,
                    rows=rows,
                    provenance_ref=f"{source_id}#csv-table:1",
                )
            )
            structures.append(
                SourceStructureElement(
                    element_id=f"{source_id}_csv_table_001",
                    source_id=source_id,
                    element_type="table",
                    role="csv_table",
                    provenance_ref=f"{source_id}#csv-table:1",
                    metadata={"row_count": len(rows), "column_count": max((len(row) for row in rows), default=0)},
                )
            )
            fragments.append(_fragment(source_id, "text", text, f"{source_id}#text:1", role="csv_text"))
        elif source_kind == "json":
            parsed = json.loads(text)
            pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
            fragments.append(_fragment(source_id, "json", pretty, f"{source_id}#json:1"))
            structures.append(_structure(source_id, "json_document", f"{source_id}#json:1", text="json", role="document"))
        else:
            fragments.append(_fragment(source_id, source_kind, text, f"{source_id}#text:1"))
            structures.append(_structure(source_id, f"{source_kind}_document", f"{source_id}#text:1", text=source_kind, role="document"))

        if not fragments and not tables and not structures and not chart_candidates:
            return _unsupported_report(
                source_id=source_id,
                source_kind=source_kind,
                title=title,
                warning="No extractable text or table content found.",
            )
        return SourceIngestionReport(
            schema_version=SOURCE_INGESTION_SCHEMA_VERSION,
            source_id=source_id,
            source_kind=source_kind,
            status="ready",
            title=title,
            fragments=fragments,
            tables=tables,
            structures=structures,
            chart_candidates=chart_candidates,
            extraction_fidelity=_basic_extraction_fidelity(
                source_id=source_id,
                source_kind=source_kind,
                extractor="stdlib_utf8_text_parser",
            ),
        )

    def _ingest_docx(self, raw_content: bytes, *, source_id: str, title: str | None) -> SourceIngestionReport:
        try:
            with ZipFile(BytesIO(raw_content)) as package:
                document_xml = package.read("word/document.xml")
                media_assets = _docx_media_assets(package, source_id=source_id)
                package_parts = set(package.namelist())
                relationship_count = _relationship_count(package, "word/_rels/document.xml.rels")
        except (BadZipFile, KeyError) as exc:
            return _unsupported_report(source_id=source_id, source_kind="docx", title=title, warning=f"Invalid DOCX package: {exc}")

        root = ET.fromstring(document_xml)
        fragments = _docx_paragraphs(root, source_id=source_id)
        tables = _docx_tables(root, source_id=source_id)
        structures = _docx_structures(root, source_id=source_id, assets=media_assets)
        if not fragments and not tables and not media_assets and not structures:
            return _unsupported_report(source_id=source_id, source_kind="docx", title=title, warning="DOCX contains no extractable paragraphs, tables, or media assets.")
        return SourceIngestionReport(
            schema_version=SOURCE_INGESTION_SCHEMA_VERSION,
            source_id=source_id,
            source_kind="docx",
            status="ready",
            title=title,
            fragments=fragments,
            tables=tables,
            assets=media_assets,
            structures=structures,
            extraction_fidelity=_package_fidelity(
                source_id=source_id,
                source_kind="docx",
                package_format="OOXML DOCX",
                extractor="stdlib_zip_xml_relationships",
                required_parts=["word/document.xml"],
                present_parts=package_parts,
                relationship_count=relationship_count,
                dependency_probes=[_dependency_probe("docx", "python-docx")],
            ),
        )

    def _ingest_pptx(self, raw_content: bytes, *, source_id: str, title: str | None) -> SourceIngestionReport:
        try:
            with ZipFile(BytesIO(raw_content)) as package:
                slide_names = sorted(
                    (name for name in package.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")),
                    key=_slide_sort_key,
                )
                slide_xml = [(index, package.read(name)) for index, name in enumerate(slide_names, start=1)]
                chart_xml = [(index, name, package.read(name)) for index, name in enumerate(sorted(path for path in package.namelist() if path.startswith("ppt/charts/chart") and path.endswith(".xml")), start=1)]
                assets = _pptx_media_assets(package, slide_names=slide_names, source_id=source_id)
                package_parts = set(package.namelist())
                relationship_count = sum(_relationship_count(package, _slide_rels_path(name)) for name in slide_names)
        except BadZipFile as exc:
            return _unsupported_report(source_id=source_id, source_kind="pptx", title=title, warning=f"Invalid PPTX package: {exc}")

        fragments: list[SourceIngestionFragment] = []
        tables: list[SourceTableCandidate] = []
        structures: list[SourceStructureElement] = []
        for slide_number, blob in slide_xml:
            root = ET.fromstring(blob)
            texts = [node.text.strip() for node in root.findall(".//a:t", _DRAWING_NS) if (node.text or "").strip()]
            structures.extend(_pptx_slide_structures(root, source_id=source_id, slide_number=slide_number))
            tables.extend(_pptx_slide_tables(root, source_id=source_id, slide_number=slide_number))
            for index, text in enumerate(texts, start=1):
                fragments.append(
                    SourceIngestionFragment(
                        fragment_id=f"{source_id}_slide_{slide_number:03d}_text_{index:03d}",
                        source_id=source_id,
                        kind="text",
                        text=text,
                        provenance_ref=f"{source_id}#slide:{slide_number}:text:{index}",
                        slide_number=slide_number,
                        role="title" if index == 1 else "text_box",
                    )
                )
        chart_candidates = _pptx_chart_candidates(chart_xml, source_id=source_id)
        if not fragments and not assets and not tables and not structures and not chart_candidates:
            return _unsupported_report(source_id=source_id, source_kind="pptx", title=title, warning="PPTX contains no extractable slide text or media assets.")
        return SourceIngestionReport(
            schema_version=SOURCE_INGESTION_SCHEMA_VERSION,
            source_id=source_id,
            source_kind="pptx",
            status="ready",
            title=title,
            fragments=fragments,
            tables=tables,
            assets=assets,
            structures=structures,
            chart_candidates=chart_candidates,
            extraction_fidelity=_package_fidelity(
                source_id=source_id,
                source_kind="pptx",
                package_format="OOXML PPTX",
                extractor="stdlib_zip_xml_relationships",
                required_parts=slide_names,
                present_parts=package_parts,
                relationship_count=relationship_count,
                dependency_probes=[_dependency_probe("pptx", "python-pptx")],
            ),
        )

    def _ingest_xlsx(self, raw_content: bytes, *, source_id: str, title: str | None) -> SourceIngestionReport:
        try:
            with ZipFile(BytesIO(raw_content)) as package:
                shared_strings = _xlsx_shared_strings(package)
                sheet_names = _xlsx_sheet_names(package)
                sheet_files = sorted(
                    (name for name in package.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")),
                    key=_sheet_sort_key,
                )
                sheet_blobs = [(index, name, package.read(name)) for index, name in enumerate(sheet_files, start=1)]
                tables = [
                    _xlsx_sheet_table(blob, source_id=source_id, sheet_name=sheet_names.get(index, f"Sheet{index}"), sheet_index=index, shared_strings=shared_strings)
                    for index, _name, blob in sheet_blobs
                ]
                structures = [
                    structure
                    for index, _name, blob in sheet_blobs
                    for structure in _xlsx_sheet_structures(blob, source_id=source_id, sheet_name=sheet_names.get(index, f"Sheet{index}"), sheet_index=index, shared_strings=shared_strings)
                ]
                chart_candidates = _xlsx_chart_candidates(package, source_id=source_id)
                assets = _zip_media_assets(package, prefix="xl/media/", source_id=source_id, owner_part="xl/workbook.xml")
                package_parts = set(package.namelist())
                relationship_count = sum(_relationship_count(package, name) for name in package.namelist() if name.startswith("xl/") and name.endswith(".rels"))
        except BadZipFile as exc:
            return _unsupported_report(source_id=source_id, source_kind="xlsx", title=title, warning=f"Invalid XLSX package: {exc}")

        tables = [table for table in tables if table.rows]
        structures = [structure for structure in structures if structure.element_type != "empty_cell"]
        fragments = [
            SourceIngestionFragment(
                fragment_id=f"{source_id}_sheet_{idx:03d}_summary",
                source_id=source_id,
                kind="sheet_summary",
                text=f"{table.sheet_name}: {len(table.rows)} extracted preview rows",
                provenance_ref=table.provenance_ref,
                sheet_name=table.sheet_name,
                role="sheet_metadata",
            )
            for idx, table in enumerate(tables, start=1)
        ]
        if not tables and not assets and not structures and not chart_candidates:
            return _unsupported_report(source_id=source_id, source_kind="xlsx", title=title, warning="XLSX contains no extractable worksheet rows or media assets.")
        return SourceIngestionReport(
            schema_version=SOURCE_INGESTION_SCHEMA_VERSION,
            source_id=source_id,
            source_kind="xlsx",
            status="ready",
            title=title,
            fragments=fragments,
            tables=tables,
            assets=assets,
            structures=structures,
            chart_candidates=chart_candidates,
            extraction_fidelity=_package_fidelity(
                source_id=source_id,
                source_kind="xlsx",
                package_format="OOXML XLSX",
                extractor="stdlib_zip_xml_relationships",
                required_parts=["xl/workbook.xml"],
                present_parts=package_parts,
                relationship_count=relationship_count,
                dependency_probes=[_dependency_probe("openpyxl", "openpyxl")],
            ),
        )

    def _ingest_pdf(self, raw_content: bytes, *, source_id: str, title: str | None) -> SourceIngestionReport:
        try:
            import fitz  # type: ignore[import-not-found]
        except Exception:
            return _unsupported_report(
                source_id=source_id,
                source_kind="pdf",
                title=title,
                warning="PDF extraction requires PyMuPDF/fitz in this deployment; KR-7D.1 does not fake PDF text or OCR.",
                extraction_fidelity=_package_fidelity(
                    source_id=source_id,
                    source_kind="pdf",
                    package_format="PDF",
                    extractor="missing_dependency",
                    dependency_probes=[_dependency_probe("fitz", "PyMuPDF/fitz")],
                ),
            )
        try:
            document = fitz.open(stream=raw_content, filetype="pdf")
        except Exception as exc:
            return _unsupported_report(source_id=source_id, source_kind="pdf", title=title, warning=f"Invalid PDF package: {exc}")
        fragments: list[SourceIngestionFragment] = []
        structures: list[SourceStructureElement] = []
        for page_index, page in enumerate(document, start=1):
            text = (page.get_text("text") or "").strip()
            structures.extend(_pdf_page_structures(page, source_id=source_id, page_number=page_index))
            if text:
                fragments.append(
                    SourceIngestionFragment(
                        fragment_id=f"{source_id}_page_{page_index:03d}",
                        source_id=source_id,
                        kind="text",
                        text=text,
                        provenance_ref=f"{source_id}#page:{page_index}",
                        page_number=page_index,
                    )
                )
        if not fragments and not structures:
            return _unsupported_report(source_id=source_id, source_kind="pdf", title=title, warning="PDF contains no extractable text through PyMuPDF; OCR is intentionally not used.")
        return SourceIngestionReport(
            schema_version=SOURCE_INGESTION_SCHEMA_VERSION,
            source_id=source_id,
            source_kind="pdf",
            status="ready",
            title=title,
            fragments=fragments,
            structures=structures,
            extraction_fidelity=_package_fidelity(
                source_id=source_id,
                source_kind="pdf",
                package_format="PDF",
                extractor="pymupdf_fitz",
                dependency_probes=[_dependency_probe("fitz", "PyMuPDF/fitz")],
            ),
        )


def detect_source_kind(*, file_type: str = "", mime_type: str = "", title: str | None = None) -> SourceKind:
    file_type = (file_type or "").strip().lower().lstrip(".")
    mime_type = (mime_type or "").strip().lower()
    if not file_type and title and "." in title:
        file_type = title.rsplit(".", 1)[-1].lower()
    if file_type in _TEXT_FILE_TYPES or mime_type.startswith("text/plain"):
        return "text"
    if file_type in _MARKDOWN_FILE_TYPES or mime_type in {"text/markdown", "text/x-markdown"}:
        return "markdown"
    if file_type in _CSV_FILE_TYPES or mime_type == "text/csv":
        return "csv"
    if file_type in _JSON_FILE_TYPES or mime_type == "application/json":
        return "json"
    if file_type in _YAML_FILE_TYPES:
        return "yaml"
    if file_type in _DOCX_FILE_TYPES or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "docx"
    if file_type in _PPTX_FILE_TYPES or mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        return "pptx"
    if file_type in _XLSX_FILE_TYPES or mime_type in {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel.sheet.macroenabled.12"}:
        return "xlsx"
    if file_type in _PDF_FILE_TYPES or mime_type == "application/pdf":
        return "pdf"
    return "unknown"


def _decode_utf8(raw_content: bytes) -> str:
    return raw_content.decode("utf-8")


def _fragment(source_id: str, kind: str, text: str, provenance_ref: str, *, role: str | None = None) -> SourceIngestionFragment:
    return SourceIngestionFragment(
        fragment_id=f"{source_id}_fragment_{_short_hash(provenance_ref)}",
        source_id=source_id,
        kind=kind,
        text=text,
        provenance_ref=provenance_ref,
        role=role,
    )


def _structure(
    source_id: str,
    element_type: str,
    provenance_ref: str,
    *,
    text: str | None = None,
    role: str | None = None,
    page_number: int | None = None,
    slide_number: int | None = None,
    sheet_name: str | None = None,
    coordinates: dict[str, float] | None = None,
    style: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> SourceStructureElement:
    return SourceStructureElement(
        element_id=f"{source_id}_structure_{_short_hash(provenance_ref)}",
        source_id=source_id,
        element_type=element_type,
        text=text,
        role=role,
        provenance_ref=provenance_ref,
        page_number=page_number,
        slide_number=slide_number,
        sheet_name=sheet_name,
        coordinates=coordinates,
        style=style,
        metadata=metadata or {},
    )


def _markdown_fragments(text: str, *, source_id: str) -> list[SourceIngestionFragment]:
    fragments: list[SourceIngestionFragment] = []
    current_heading = "document"
    current_level = None
    current_lines: list[str] = []
    index = 0

    def flush() -> None:
        nonlocal index, current_lines
        body = "\n".join(line for line in current_lines if line.strip()).strip()
        if not body:
            current_lines = []
            return
        index += 1
        fragments.append(
            SourceIngestionFragment(
                fragment_id=f"{source_id}_md_section_{index:03d}",
                source_id=source_id,
                kind="markdown_section",
                text=body,
                provenance_ref=f"{source_id}#markdown-section:{index}",
                heading_level=current_level,
                role=current_heading,
            )
        )
        current_lines = []

    for line in text.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            flush()
            current_level = len(heading.group(1))
            current_heading = heading.group(2).strip()
        current_lines.append(line)
    flush()
    if not fragments and text.strip():
        fragments.append(_fragment(source_id, "markdown", text.strip(), f"{source_id}#markdown:1"))
    return fragments


def _markdown_tables(text: str, *, source_id: str) -> list[SourceTableCandidate]:
    tables: list[SourceTableCandidate] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        if "|" not in lines[index]:
            index += 1
            continue
        block: list[str] = []
        while index < len(lines) and "|" in lines[index]:
            block.append(lines[index])
            index += 1
        rows = [_pipe_row(line) for line in block if not _is_markdown_separator(line)]
        rows = [row for row in rows if row]
        if len(rows) >= 2:
            tables.append(
                SourceTableCandidate(
                    table_id=f"{source_id}_markdown_table_{len(tables)+1:03d}",
                    source_id=source_id,
                    rows=rows,
                    provenance_ref=f"{source_id}#markdown-table:{len(tables)+1}",
                )
            )
    return tables




def _markdown_structures(
    text: str,
    *,
    source_id: str,
    tables: list[SourceTableCandidate],
) -> list[SourceStructureElement]:
    structures: list[SourceStructureElement] = []
    in_code_block = False
    code_lines: list[str] = []
    code_language = ""
    code_start_line = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        fence = re.match(r"^```\s*([A-Za-z0-9_+-]*)", line.strip())
        if fence:
            if in_code_block:
                provenance_ref = f"{source_id}#markdown-code:{code_start_line}-{line_number}"
                structures.append(
                    _structure(
                        source_id,
                        "code_block",
                        provenance_ref,
                        text="\n".join(code_lines),
                        role="code",
                        metadata={"language": code_language, "start_line": code_start_line, "end_line": line_number},
                    )
                )
                in_code_block = False
                code_lines = []
                code_language = ""
                code_start_line = 0
            else:
                in_code_block = True
                code_language = fence.group(1) or "plain"
                code_start_line = line_number
            continue
        if in_code_block:
            code_lines.append(line)
            continue
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            structures.append(
                _structure(
                    source_id,
                    "heading",
                    f"{source_id}#markdown-heading:{line_number}",
                    text=title,
                    role="heading",
                    style=f"h{level}",
                    metadata={"line_number": line_number, "level": level},
                )
            )
        for image_index, image in enumerate(re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", line), start=1):
            structures.append(
                _structure(
                    source_id,
                    "image_ref",
                    f"{source_id}#markdown-image:{line_number}:{image_index}",
                    text=image.group(1),
                    role="image_reference",
                    metadata={"line_number": line_number, "target": image.group(2)},
                )
            )
    for table in tables:
        structures.append(
            _structure(
                source_id,
                "table",
                table.provenance_ref,
                role="markdown_table",
                metadata={"row_count": len(table.rows), "column_count": max((len(row) for row in table.rows), default=0)},
            )
        )
    return structures


def _pipe_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_markdown_separator(line: str) -> bool:
    stripped = line.strip().strip("|")
    return bool(stripped) and all(set(cell.strip()) <= {"-", ":"} for cell in stripped.split("|"))


def _csv_rows(text: str) -> list[list[str]]:
    return [[cell.strip() for cell in row] for row in csv.reader(StringIO(text)) if any(cell.strip() for cell in row)]


def _docx_paragraphs(root: ET.Element, *, source_id: str) -> list[SourceIngestionFragment]:
    fragments: list[SourceIngestionFragment] = []
    for index, paragraph in enumerate(root.findall(".//w:p", _WORD_NS), start=1):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", _WORD_NS)]
        text = "".join(texts).strip()
        if not text:
            continue
        style = _docx_paragraph_style(paragraph)
        heading_level = _heading_level_from_style(style)
        fragments.append(
            SourceIngestionFragment(
                fragment_id=f"{source_id}_docx_paragraph_{len(fragments)+1:03d}",
                source_id=source_id,
                kind="paragraph",
                text=text,
                provenance_ref=f"{source_id}#docx-paragraph:{index}",
                heading_level=heading_level,
                role="heading" if heading_level else "paragraph",
            )
        )
    return fragments


def _docx_tables(root: ET.Element, *, source_id: str) -> list[SourceTableCandidate]:
    tables: list[SourceTableCandidate] = []
    for table_index, table in enumerate(root.findall(".//w:tbl", _WORD_NS), start=1):
        rows: list[list[str]] = []
        for row in table.findall(".//w:tr", _WORD_NS):
            cells: list[str] = []
            for cell in row.findall(".//w:tc", _WORD_NS):
                texts = [node.text or "" for node in cell.findall(".//w:t", _WORD_NS)]
                cells.append("".join(texts).strip())
            if any(cells):
                rows.append(cells)
        if rows:
            tables.append(
                SourceTableCandidate(
                    table_id=f"{source_id}_docx_table_{table_index:03d}",
                    source_id=source_id,
                    rows=rows,
                    provenance_ref=f"{source_id}#docx-table:{table_index}",
                )
            )
    return tables


def _docx_structures(
    root: ET.Element,
    *,
    source_id: str,
    assets: list[SourceAsset],
) -> list[SourceStructureElement]:
    structures: list[SourceStructureElement] = []
    for index, paragraph in enumerate(root.findall(".//w:p", _WORD_NS), start=1):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", _WORD_NS)).strip()
        if not text:
            continue
        style = _docx_paragraph_style(paragraph)
        heading_level = _heading_level_from_style(style)
        role = "caption" if _is_docx_caption(text, style) else ("heading" if heading_level else "paragraph")
        structures.append(
            _structure(
                source_id,
                "paragraph",
                f"{source_id}#docx-paragraph:{index}",
                text=text,
                role=role,
                style=style,
                metadata={"heading_level": heading_level},
            )
        )
    for table_index, table in enumerate(root.findall(".//w:tbl", _WORD_NS), start=1):
        row_count = len(table.findall(".//w:tr", _WORD_NS))
        structures.append(
            _structure(
                source_id,
                "table",
                f"{source_id}#docx-table:{table_index}",
                role="docx_table",
                metadata={"row_count": row_count},
            )
        )
    for asset in assets:
        structures.append(
            _structure(
                source_id,
                "inline_image",
                asset.provenance_ref,
                role="source_asset",
                metadata={"package_path": asset.path, "mime_type": asset.mime_type, "size_bytes": asset.size_bytes},
            )
        )
    return structures


def _docx_paragraph_style(paragraph: ET.Element) -> str | None:
    style_node = paragraph.find(".//w:pStyle", _WORD_NS)
    return style_node.attrib.get(f"{{{_WORD_NS['w']}}}val") if style_node is not None else None


def _is_docx_caption(text: str, style: str | None) -> bool:
    if style and style.lower() == "caption":
        return True
    return bool(re.match(r"^(figure|fig\.|table)\s+[0-9ivx]+[:.\s-]", text.strip(), flags=re.IGNORECASE))


def _heading_level_from_style(style: str | None) -> int | None:
    if not style:
        return None
    match = re.search(r"heading\s*([1-6])|Heading([1-6])", style, flags=re.IGNORECASE)
    if not match:
        return None
    return int(next(group for group in match.groups() if group))


def _docx_media_assets(package: ZipFile, *, source_id: str) -> list[SourceAsset]:
    relationships = _ooxml_relationships(package, "word/_rels/document.xml.rels", owner_part="word/document.xml")
    by_path = _relationships_by_package_path(relationships)
    return _zip_media_assets(
        package,
        prefix="word/media/",
        source_id=source_id,
        owner_part="word/document.xml",
        relationships_by_package_path=by_path,
    )


def _pptx_media_assets(package: ZipFile, *, slide_names: list[str], source_id: str) -> list[SourceAsset]:
    assets: list[SourceAsset] = []
    seen: set[tuple[str, int | None, str | None]] = set()
    for slide_number, slide_name in enumerate(slide_names, start=1):
        relationships = _ooxml_relationships(package, _slide_rels_path(slide_name), owner_part=slide_name)
        by_path = _relationships_by_package_path(relationships)
        slide_assets = _zip_media_assets(
            package,
            prefix="ppt/media/",
            source_id=source_id,
            owner_part=slide_name,
            relationships_by_package_path=by_path,
            slide_number=slide_number,
            asset_id_offset=len(assets),
        )
        for asset in slide_assets:
            key = (asset.path, asset.slide_number, asset.relationship_id)
            if key not in seen:
                assets.append(asset)
                seen.add(key)
    # Preserve unreferenced media honestly as orphan assets instead of dropping bytes.
    referenced_paths = {asset.path for asset in assets}
    orphan_assets = _zip_media_assets(
        package,
        prefix="ppt/media/",
        source_id=source_id,
        owner_part="ppt/presentation.xml",
        relationship_role="orphan_package_media",
        asset_id_offset=len(assets),
        exclude_paths=referenced_paths,
    )
    return [*assets, *orphan_assets]


def _zip_media_assets(
    package: ZipFile,
    *,
    prefix: str,
    source_id: str,
    owner_part: str | None = None,
    relationships_by_package_path: dict[str, list[dict[str, str]]] | None = None,
    relationship_role: str | None = None,
    page_number: int | None = None,
    slide_number: int | None = None,
    sheet_name: str | None = None,
    asset_id_offset: int = 0,
    exclude_paths: set[str] | None = None,
) -> list[SourceAsset]:
    assets: list[SourceAsset] = []
    excluded = exclude_paths or set()
    relationships_by_package_path = relationships_by_package_path or {}
    media_paths = sorted(
        path
        for path in package.namelist()
        if path.startswith(prefix) and not path.endswith("/") and path not in excluded
    )
    for local_index, name in enumerate(media_paths, start=1):
        index = asset_id_offset + local_index
        blob = package.read(name)
        width_px, height_px, dimension_source = _image_dimensions_from_bytes(blob)
        relationships = relationships_by_package_path.get(name, [])
        relationship = relationships[0] if relationships else {}
        metadata = {
            "owner_part": owner_part,
            "relationship_target": relationship.get("target"),
            "relationship_type": relationship.get("type"),
            "relationship_role": relationship_role or ("relationship_resolved" if relationship else "package_media"),
            "dimension_source": dimension_source,
        }
        assets.append(
            SourceAsset(
                asset_id=f"{source_id}_asset_{index:03d}",
                source_id=source_id,
                asset_type="image",
                path=name,
                provenance_ref=f"{source_id}#asset:{index}:{name}",
                checksum_sha256=hashlib.sha256(blob).hexdigest(),
                size_bytes=len(blob),
                mime_type=_mime_type_from_name(name),
                page_number=page_number,
                slide_number=slide_number,
                sheet_name=sheet_name,
                width_px=width_px,
                height_px=height_px,
                content_bytes=blob,
                relationship_id=relationship.get("id"),
                owner_part=owner_part,
                metadata={key: value for key, value in metadata.items() if value is not None},
            )
        )
    return assets


def _ooxml_relationships(package: ZipFile, rels_path: str, *, owner_part: str) -> dict[str, dict[str, str]]:
    try:
        rels_xml = package.read(rels_path)
    except KeyError:
        return {}
    try:
        root = ET.fromstring(rels_xml)
    except ET.ParseError:
        return {}
    relationships: dict[str, dict[str, str]] = {}
    for rel in root.findall("rel:Relationship", _REL_NS):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target", "")
        if not rel_id or not target:
            continue
        relationships[rel_id] = {
            "id": rel_id,
            "target": target,
            "type": rel.attrib.get("Type", ""),
            "package_path": _normalize_ooxml_target(owner_part, target),
        }
    return relationships


def _relationships_by_package_path(relationships: dict[str, dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_path: dict[str, list[dict[str, str]]] = {}
    for relationship in relationships.values():
        package_path = relationship.get("package_path")
        if package_path:
            by_path.setdefault(package_path, []).append(relationship)
    return by_path


def _normalize_ooxml_target(owner_part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    owner_dir = posixpath.dirname(owner_part)
    return posixpath.normpath(posixpath.join(owner_dir, target)).lstrip("/")


def _relationship_count(package: ZipFile, rels_path: str) -> int:
    try:
        root = ET.fromstring(package.read(rels_path))
    except (KeyError, ET.ParseError):
        return 0
    return len(root.findall("rel:Relationship", _REL_NS))


def _slide_rels_path(slide_name: str) -> str:
    slide_file = slide_name.rsplit("/", 1)[-1]
    return f"ppt/slides/_rels/{slide_file}.rels"


def _image_dimensions_from_bytes(blob: bytes) -> tuple[int | None, int | None, str]:
    try:
        from PIL import Image  # type: ignore[import-not-found]
    except Exception:
        return None, None, "pillow_unavailable"
    try:
        with Image.open(BytesIO(blob)) as image:
            return int(image.width), int(image.height), "pillow"
    except Exception:
        return None, None, "unreadable_image"


def _pptx_slide_structures(root: ET.Element, *, source_id: str, slide_number: int) -> list[SourceStructureElement]:
    structures: list[SourceStructureElement] = [
        _structure(
            source_id,
            "slide",
            f"{source_id}#slide:{slide_number}",
            role="slide",
            slide_number=slide_number,
        )
    ]
    for shape_index, shape in enumerate(root.findall(".//p:sp", _PRESENTATION_NS), start=1):
        texts = [node.text.strip() for node in shape.findall(".//a:t", _DRAWING_NS) if (node.text or "").strip()]
        if not texts:
            continue
        c_nv_pr = shape.find(".//p:cNvPr", _PRESENTATION_NS)
        placeholder = shape.find(".//p:ph", _PRESENTATION_NS)
        placeholder_type = placeholder.attrib.get("type") if placeholder is not None else None
        shape_name = c_nv_pr.attrib.get("name") if c_nv_pr is not None else None
        shape_id = c_nv_pr.attrib.get("id") if c_nv_pr is not None else None
        structures.append(
            _structure(
                source_id,
                "text_box",
                f"{source_id}#slide:{slide_number}:shape:{shape_index}",
                text="\n".join(texts),
                role=placeholder_type or ("title" if shape_index == 1 else "text_box"),
                slide_number=slide_number,
                metadata={"shape_name": shape_name, "shape_id": shape_id, "text_run_count": len(texts)},
            )
        )
    for table_index, table in enumerate(root.findall(".//a:tbl", _DRAWING_NS), start=1):
        structures.append(
            _structure(
                source_id,
                "table",
                f"{source_id}#slide:{slide_number}:table:{table_index}",
                role="pptx_table",
                slide_number=slide_number,
                metadata={"row_count": len(table.findall(".//a:tr", _DRAWING_NS))},
            )
        )
    return structures


def _pptx_slide_tables(root: ET.Element, *, source_id: str, slide_number: int) -> list[SourceTableCandidate]:
    tables: list[SourceTableCandidate] = []
    for table_index, table in enumerate(root.findall(".//a:tbl", _DRAWING_NS), start=1):
        rows: list[list[str]] = []
        for row in table.findall(".//a:tr", _DRAWING_NS):
            cells: list[str] = []
            for cell in row.findall("a:tc", _DRAWING_NS):
                cells.append("".join(node.text or "" for node in cell.findall(".//a:t", _DRAWING_NS)).strip())
            if any(cells):
                rows.append(cells)
        if rows:
            tables.append(
                SourceTableCandidate(
                    table_id=f"{source_id}_pptx_slide_{slide_number:03d}_table_{table_index:03d}",
                    source_id=source_id,
                    rows=rows,
                    provenance_ref=f"{source_id}#slide:{slide_number}:table:{table_index}",
                    slide_number=slide_number,
                )
            )
    return tables


def _pptx_chart_candidates(chart_xml: list[tuple[int, str, bytes]], *, source_id: str) -> list[SourceChartDataCandidate]:
    candidates: list[SourceChartDataCandidate] = []
    for index, name, blob in chart_xml:
        try:
            root = ET.fromstring(blob)
        except ET.ParseError:
            continue
        data_refs = [node.text or "" for node in root.findall(".//c:f", _CHART_NS) if (node.text or "").strip()]
        chart_type = _chart_type_from_xml(root)
        candidates.append(
            SourceChartDataCandidate(
                candidate_id=f"{source_id}_pptx_chart_{index:03d}",
                source_id=source_id,
                chart_type=chart_type,
                provenance_ref=f"{source_id}#pptx-chart:{index}:{name}",
                data_refs=data_refs,
                metadata={"package_path": name},
            )
        )
    return candidates


def _xlsx_shared_strings(package: ZipFile) -> list[str]:
    try:
        xml = package.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(xml)
    values: list[str] = []
    for item in root.findall(".//main:si", _SPREADSHEET_NS):
        values.append("".join(node.text or "" for node in item.findall(".//main:t", _SPREADSHEET_NS)))
    return values


def _xlsx_sheet_names(package: ZipFile) -> dict[int, str]:
    try:
        workbook_xml = package.read("xl/workbook.xml")
    except KeyError:
        return {}
    root = ET.fromstring(workbook_xml)
    names: dict[int, str] = {}
    for index, sheet in enumerate(root.findall(".//main:sheets/main:sheet", _SPREADSHEET_NS), start=1):
        names[index] = sheet.attrib.get("name", f"Sheet{index}")
    return names


def _xlsx_sheet_table(
    sheet_xml: bytes,
    *,
    source_id: str,
    sheet_name: str,
    sheet_index: int,
    shared_strings: list[str],
) -> SourceTableCandidate:
    root = ET.fromstring(sheet_xml)
    rows: list[list[str]] = []
    has_formula = False
    for row in root.findall(".//main:sheetData/main:row", _SPREADSHEET_NS)[:20]:
        cells: list[str] = []
        for cell in row.findall("main:c", _SPREADSHEET_NS)[:20]:
            formula = cell.find("main:f", _SPREADSHEET_NS)
            if formula is not None:
                has_formula = True
                cells.append(f"={formula.text or ''}")
                continue
            value = cell.find("main:v", _SPREADSHEET_NS)
            if value is None or value.text is None:
                cells.append("")
                continue
            if cell.attrib.get("t") == "s":
                try:
                    cells.append(shared_strings[int(value.text)])
                except (ValueError, IndexError):
                    cells.append(value.text)
            else:
                cells.append(value.text)
        if any(cell.strip() for cell in cells):
            rows.append(cells)
    return SourceTableCandidate(
        table_id=f"{source_id}_xlsx_sheet_{sheet_index:03d}",
        source_id=source_id,
        rows=rows,
        provenance_ref=f"{source_id}#xlsx-sheet:{sheet_index}",
        sheet_name=sheet_name,
        has_formula=has_formula,
    )


def _xlsx_sheet_structures(
    sheet_xml: bytes,
    *,
    source_id: str,
    sheet_name: str,
    sheet_index: int,
    shared_strings: list[str],
) -> list[SourceStructureElement]:
    root = ET.fromstring(sheet_xml)
    rows = root.findall(".//main:sheetData/main:row", _SPREADSHEET_NS)
    structures: list[SourceStructureElement] = [
        _structure(
            source_id,
            "worksheet",
            f"{source_id}#xlsx-sheet:{sheet_index}",
            role="worksheet",
            sheet_name=sheet_name,
            metadata={"row_count": len(rows)},
        )
    ]
    formula_index = 0
    for row in rows[:50]:
        for cell in row.findall("main:c", _SPREADSHEET_NS)[:50]:
            formula = cell.find("main:f", _SPREADSHEET_NS)
            if formula is None:
                continue
            formula_index += 1
            cell_ref = cell.attrib.get("r")
            structures.append(
                _structure(
                    source_id,
                    "formula",
                    f"{source_id}#xlsx-sheet:{sheet_index}:formula:{formula_index}",
                    text=f"={formula.text or ''}",
                    role="formula",
                    sheet_name=sheet_name,
                    metadata={"cell_ref": cell_ref},
                )
            )
    return structures


def _xlsx_chart_candidates(package: ZipFile, *, source_id: str) -> list[SourceChartDataCandidate]:
    candidates: list[SourceChartDataCandidate] = []
    chart_files = sorted(path for path in package.namelist() if path.startswith("xl/charts/chart") and path.endswith(".xml"))
    for index, name in enumerate(chart_files, start=1):
        try:
            root = ET.fromstring(package.read(name))
        except ET.ParseError:
            continue
        data_refs = [node.text or "" for node in root.findall(".//c:f", _CHART_NS) if (node.text or "").strip()]
        candidates.append(
            SourceChartDataCandidate(
                candidate_id=f"{source_id}_xlsx_chart_{index:03d}",
                source_id=source_id,
                chart_type=_chart_type_from_xml(root),
                provenance_ref=f"{source_id}#xlsx-chart:{index}:{name}",
                data_refs=data_refs,
                metadata={"package_path": name},
            )
        )
    return candidates


def _chart_type_from_xml(root: ET.Element) -> str:
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name.endswith("Chart") and local_name != "chart":
            return local_name
    return "unknown_chart"


def _pdf_page_structures(page: Any, *, source_id: str, page_number: int) -> list[SourceStructureElement]:
    structures: list[SourceStructureElement] = []
    rect = getattr(page, "rect", None)
    metadata: dict[str, Any] = {}
    if rect is not None:
        metadata = {"width": float(getattr(rect, "width", 0.0)), "height": float(getattr(rect, "height", 0.0))}
    structures.append(
        _structure(
            source_id,
            "page",
            f"{source_id}#page:{page_number}",
            role="pdf_page",
            page_number=page_number,
            metadata=metadata,
        )
    )
    try:
        page_dict = page.get_text("dict") or {}
    except Exception:
        return structures
    for block_index, block in enumerate(page_dict.get("blocks", []), start=1):
        bbox = block.get("bbox")
        coordinates = None
        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            coordinates = {"x0": float(bbox[0]), "y0": float(bbox[1]), "x1": float(bbox[2]), "y1": float(bbox[3])}
        block_type = "image_block" if block.get("type") == 1 else "text_block"
        block_text = _pdf_block_text(block)
        structures.append(
            _structure(
                source_id,
                block_type,
                f"{source_id}#page:{page_number}:block:{block_index}",
                text=block_text[:500] if block_text else None,
                role=block_type,
                page_number=page_number,
                coordinates=coordinates,
                metadata={"block_type": block.get("type")},
            )
        )
    return structures


def _pdf_block_text(block: dict[str, Any]) -> str:
    lines: list[str] = []
    for line in block.get("lines", []) or []:
        spans = line.get("spans", []) or []
        text = "".join(str(span.get("text", "")) for span in spans).strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def _slide_sort_key(name: str) -> tuple[int, str]:
    stem = name.rsplit("/", 1)[-1].removesuffix(".xml")
    suffix = stem.replace("slide", "")
    return (int(suffix) if suffix.isdigit() else 10**9, name)


def _sheet_sort_key(name: str) -> tuple[int, str]:
    stem = name.rsplit("/", 1)[-1].removesuffix(".xml")
    suffix = stem.replace("sheet", "")
    return (int(suffix) if suffix.isdigit() else 10**9, name)



def _dependency_probe(module_name: str, label: str) -> dict[str, Any]:
    spec = importlib.util.find_spec(module_name)
    return {"name": label, "module": module_name, "available": spec is not None}


def _basic_extraction_fidelity(*, source_id: str, source_kind: SourceKind, extractor: str) -> dict[str, Any]:
    return {
        "schema_version": SOURCE_EXTRACTION_FIDELITY_SCHEMA_VERSION,
        "source_id": source_id,
        "source_kind": source_kind,
        "extractor": extractor,
        "package_format": "plain_text",
        "dependency_backed_extractors": [],
        "required_parts": [],
        "present_required_parts": [],
        "missing_required_parts": [],
        "relationship_count": 0,
        "fidelity_notes": ["text-like extraction uses deterministic UTF-8 parsing only"],
    }


def _package_fidelity(
    *,
    source_id: str,
    source_kind: SourceKind,
    package_format: str,
    extractor: str,
    required_parts: list[str] | None = None,
    present_parts: set[str] | None = None,
    relationship_count: int = 0,
    dependency_probes: list[dict[str, Any]] | None = None,
    fidelity_notes: list[str] | None = None,
) -> dict[str, Any]:
    required = required_parts or []
    present = sorted(part for part in required if present_parts is None or part in present_parts)
    missing = sorted(part for part in required if present_parts is not None and part not in present_parts)
    probes = dependency_probes or []
    return {
        "schema_version": SOURCE_EXTRACTION_FIDELITY_SCHEMA_VERSION,
        "source_id": source_id,
        "source_kind": source_kind,
        "extractor": extractor,
        "package_format": package_format,
        "dependency_backed_extractors": probes,
        "required_parts": required,
        "present_required_parts": present,
        "missing_required_parts": missing,
        "relationship_count": relationship_count,
        "fidelity_notes": fidelity_notes or [
            "package extraction resolves OOXML relationships when available",
            "missing optional dependencies are reported through dependency_backed_extractors",
        ],
    }


def _default_extraction_fidelity(report: SourceIngestionReport) -> dict[str, Any]:
    return {
        "schema_version": SOURCE_EXTRACTION_FIDELITY_SCHEMA_VERSION,
        "source_id": report.source_id,
        "source_kind": report.source_kind,
        "extractor": "default_report_wrapper",
        "package_format": "unknown",
        "dependency_backed_extractors": [],
        "required_parts": [],
        "present_required_parts": [],
        "missing_required_parts": [],
        "relationship_count": 0,
        "fidelity_notes": ["no package-specific fidelity metadata was attached before manifest wrapping"],
    }

def _with_manifests(report: SourceIngestionReport) -> SourceIngestionReport:
    provenance_manifest = {
        "schema_version": "source_ingestion_provenance.v1",
        "source_id": report.source_id,
        "fragment_count": len(report.fragments),
        "table_count": len(report.tables),
        "asset_count": len(report.assets),
        "structure_count": len(report.structures),
        "chart_candidate_count": len(report.chart_candidates),
        "provenance_refs": [
            *(fragment.provenance_ref for fragment in report.fragments),
            *(table.provenance_ref for table in report.tables),
            *(asset.provenance_ref for asset in report.assets),
            *(structure.provenance_ref for structure in report.structures),
            *(candidate.provenance_ref for candidate in report.chart_candidates),
        ],
    }
    source_asset_registry = {
        "schema_version": SOURCE_ASSET_REGISTRY_SCHEMA_VERSION,
        "source_id": report.source_id,
        "assets": [asset.as_dict() for asset in report.assets],
    }
    return SourceIngestionReport(
        schema_version=report.schema_version,
        source_id=report.source_id,
        source_kind=report.source_kind,
        status=report.status,
        title=report.title,
        fragments=report.fragments,
        tables=report.tables,
        assets=report.assets,
        structures=report.structures,
        chart_candidates=report.chart_candidates,
        warnings=report.warnings,
        errors=report.errors,
        provenance_manifest=provenance_manifest,
        source_asset_registry=source_asset_registry,
        extraction_fidelity=report.extraction_fidelity or _default_extraction_fidelity(report),
    )


def _unsupported_report(
    *,
    source_id: str,
    source_kind: SourceKind,
    title: str | None,
    warning: str,
    extraction_fidelity: dict[str, Any] | None = None,
) -> SourceIngestionReport:
    return _with_manifests(
        SourceIngestionReport(
            schema_version=SOURCE_INGESTION_SCHEMA_VERSION,
            source_id=source_id,
            source_kind=source_kind,
            status="unsupported",
            title=title,
            warnings=[warning],
            extraction_fidelity=extraction_fidelity or {},
        )
    )


def _failed_report(*, source_id: str, source_kind: SourceKind, title: str | None, error: str) -> SourceIngestionReport:
    return _with_manifests(
        SourceIngestionReport(
            schema_version=SOURCE_INGESTION_SCHEMA_VERSION,
            source_id=source_id,
            source_kind=source_kind,
            status="failed",
            title=title,
            errors=[error],
        )
    )


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _mime_type_from_name(name: str) -> str | None:
    suffix = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "webp": "image/webp",
        "emf": "image/x-emf",
    }.get(suffix)


__all__ = [
    "SOURCE_ASSET_REGISTRY_SCHEMA_VERSION",
    "SOURCE_STRUCTURE_SCHEMA_VERSION",
    "SOURCE_INGESTION_SCHEMA_VERSION",
    "OfflineSourceIngestionEngine",
    "SourceAsset",
    "SourceIngestionFragment",
    "SourceIngestionReport",
    "SourceStructureElement",
    "SourceTableCandidate",
    "SourceChartDataCandidate",
    "detect_source_kind",
]
