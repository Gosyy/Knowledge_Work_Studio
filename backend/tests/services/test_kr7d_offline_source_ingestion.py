from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

from backend.app.services.slides_service.offline_source_ingestion import (
    SOURCE_ASSET_REGISTRY_SCHEMA_VERSION,
    SOURCE_INGESTION_SCHEMA_VERSION,
    OfflineSourceIngestionEngine,
    detect_source_kind,
)


def _zip(entries: dict[str, str | bytes]) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w") as package:
        for path, content in entries.items():
            package.writestr(path, content)
    return output.getvalue()


def test_kr7d_markdown_ingestion_extracts_headings_tables_and_provenance() -> None:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Summary\nImportant point\n\n| KPI | Value |\n| --- | --- |\n| Cost | 42 |\n",
        source_id="src_md",
        file_type="md",
        title="brief.md",
    )

    assert report.schema_version == SOURCE_INGESTION_SCHEMA_VERSION
    assert report.status == "ready"
    assert report.source_kind == "markdown"
    assert report.fragments[0].role == "Summary"
    assert report.fragments[0].heading_level == 1
    assert report.tables[0].rows == [["KPI", "Value"], ["Cost", "42"]]
    assert report.provenance_manifest["fragment_count"] == 1
    assert "src_md#markdown-table:1" in report.provenance_manifest["provenance_refs"]


def test_kr7d_docx_ingestion_extracts_paragraph_table_and_image_asset() -> None:
    docx = _zip(
        {
            "word/document.xml": """
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
              <w:body>
                <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Executive title</w:t></w:r></w:p>
                <w:p><w:r><w:t>Body paragraph</w:t></w:r></w:p>
                <w:tbl><w:tr><w:tc><w:p><w:r><w:t>A</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>B</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
              </w:body>
            </w:document>
            """,
            "word/media/image1.png": b"png-bytes",
        }
    )

    report = OfflineSourceIngestionEngine().ingest_bytes(docx, source_id="src_docx", file_type="docx")

    assert report.status == "ready"
    assert report.fragments[0].heading_level == 1
    assert report.fragments[1].text == "Body paragraph"
    assert report.tables[0].rows == [["A", "B"]]
    assert report.assets[0].path == "word/media/image1.png"
    assert report.assets[0].checksum_sha256
    assert report.source_asset_registry["schema_version"] == SOURCE_ASSET_REGISTRY_SCHEMA_VERSION


def test_kr7d_pptx_ingestion_extracts_slide_text_and_media_assets() -> None:
    pptx = _zip(
        {
            "ppt/slides/slide1.xml": """
            <p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
              <p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Slide title</a:t></a:r></a:p><a:p><a:r><a:t>Point one</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld>
            </p:sld>
            """,
            "ppt/media/image1.jpeg": b"jpeg-bytes",
        }
    )

    report = OfflineSourceIngestionEngine().ingest_bytes(pptx, source_id="src_pptx", file_type="pptx")

    assert report.status == "ready"
    assert [fragment.text for fragment in report.fragments] == ["Slide title", "Point one"]
    assert report.fragments[0].slide_number == 1
    assert report.assets[0].mime_type == "image/jpeg"


def test_kr7d_xlsx_ingestion_extracts_table_preview_and_formula_flag() -> None:
    xlsx = _zip(
        {
            "xl/workbook.xml": """
            <workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Data" sheetId="1" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></sheets></workbook>
            """,
            "xl/sharedStrings.xml": """
            <sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>Revenue</t></si><si><t>Cost</t></si></sst>
            """,
            "xl/worksheets/sheet1.xml": """
            <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
              <row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1"><v>100</v></c></row>
              <row r="2"><c r="A2" t="s"><v>1</v></c><c r="B2"><f>B1*0.5</f><v>50</v></c></row>
            </sheetData></worksheet>
            """,
        }
    )

    report = OfflineSourceIngestionEngine().ingest_bytes(xlsx, source_id="src_xlsx", file_type="xlsx")

    assert report.status == "ready"
    assert report.tables[0].sheet_name == "Data"
    assert report.tables[0].rows == [["Revenue", "100"], ["Cost", "=B1*0.5"]]
    assert report.tables[0].has_formula is True
    assert report.fragments[0].role == "sheet_metadata"


def test_kr7d_pdf_without_runtime_dependency_reports_unsupported_not_fake_success() -> None:
    report = OfflineSourceIngestionEngine().ingest_bytes(b"%PDF-1.4", source_id="src_pdf", file_type="pdf")

    assert report.status in {"unsupported", "failed"}
    assert report.fragments == []
    assert report.tables == []
    assert report.provenance_manifest["fragment_count"] == 0


def test_kr7d_detect_source_kind_uses_file_type_mime_and_title_without_network() -> None:
    assert detect_source_kind(file_type="", mime_type="text/markdown", title=None) == "markdown"
    assert detect_source_kind(file_type="", mime_type="", title="deck.pptx") == "pptx"
    assert detect_source_kind(file_type="unknown", mime_type="application/octet-stream", title=None) == "unknown"


def test_kr7d_source_asset_registry_persists_extracted_asset_bytes(tmp_path) -> None:
    import json
    from pathlib import Path

    from backend.app.services.slides_service.source_asset_registry import (
        SOURCE_ASSET_STORAGE_SCHEMA_VERSION,
        SourceAssetRegistryStore,
    )

    docx = _zip(
        {
            "word/document.xml": """
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
              <w:body><w:p><w:r><w:t>Image source</w:t></w:r></w:p></w:body>
            </w:document>
            """,
            "word/media/image1.png": b"png-bytes-for-storage",
        }
    )

    report = OfflineSourceIngestionEngine().ingest_bytes(docx, source_id="src docx", file_type="docx")
    result = SourceAssetRegistryStore(tmp_path / "source_assets").persist_report(report)

    assert result.schema_version == SOURCE_ASSET_STORAGE_SCHEMA_VERSION
    assert result.status == "ready"
    assert len(result.assets) == 1
    stored = result.assets[0]
    assert stored.storage_uri == "source-asset://src_docx/src_docx_asset_001"
    assert not Path(stored.relative_path).is_absolute()
    assert stored.relative_path == "src_docx/assets/src_docx_asset_001.png"
    assert (tmp_path / "source_assets" / stored.relative_path).read_bytes() == b"png-bytes-for-storage"

    manifest_path = tmp_path / "source_assets" / result.registry_manifest_relative_path
    report_path = tmp_path / "source_assets" / result.ingestion_report_relative_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == SOURCE_ASSET_STORAGE_SCHEMA_VERSION
    assert manifest["assets"][0]["relative_path"] == stored.relative_path
    assert "content_bytes" not in json.dumps(report_payload, ensure_ascii=False)
    assert str(tmp_path) not in json.dumps(manifest, ensure_ascii=False)


def test_kr7d_source_asset_registry_empty_report_is_honest(tmp_path) -> None:
    from backend.app.services.slides_service.source_asset_registry import SourceAssetRegistryStore

    report = OfflineSourceIngestionEngine().ingest_bytes(b"plain text only", source_id="src_text", file_type="txt")
    result = SourceAssetRegistryStore(tmp_path / "source_assets").persist_report(report)

    assert result.status == "empty"
    assert result.assets == []
    assert result.warnings == ["No extracted assets were present in the ingestion report."]
