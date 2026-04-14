from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

BUILDER = 'from __future__ import annotations\n\nfrom html import escape\nfrom io import BytesIO\nfrom zipfile import ZIP_DEFLATED, ZipFile\n\n\n_WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"\n\n\ndef build_docx_package(document_text: str) -> bytes:\n    """Build a minimal valid DOCX OPC package from plain document text.\n\n    This deterministic builder owns binary DOCX correctness. It intentionally\n    does not rely on LLM output or text bytes masquerading as .docx content.\n    """\n\n    buffer = BytesIO()\n    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as package:\n        package.writestr("[Content_Types].xml", _content_types_xml())\n        package.writestr("_rels/.rels", _root_relationships_xml())\n        package.writestr("word/document.xml", _document_xml(document_text))\n        package.writestr("word/styles.xml", _styles_xml())\n    return buffer.getvalue()\n\n\ndef _content_types_xml() -> str:\n    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n  <Default Extension="xml" ContentType="application/xml"/>\n  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>\n</Types>\n"""\n\n\ndef _root_relationships_xml() -> str:\n    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>\n</Relationships>\n"""\n\n\ndef _document_xml(document_text: str) -> str:\n    paragraphs = document_text.splitlines() or [""]\n    paragraph_xml = "\\n".join(_paragraph_xml(line) for line in paragraphs)\n    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document xmlns:w="{_WORD_NS}">\n  <w:body>\n{paragraph_xml}\n    <w:sectPr>\n      <w:pgSz w:w="12240" w:h="15840"/>\n      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>\n    </w:sectPr>\n  </w:body>\n</w:document>\n"""\n\n\ndef _paragraph_xml(text: str) -> str:\n    style = ""\n    visible_text = text\n    if text.startswith("# "):\n        style = \'<w:pPr><w:pStyle w:val="Heading1"/></w:pPr>\'\n        visible_text = text[2:]\n    return f"""    <w:p>\n      {style}\n      <w:r>\n        {_text_xml(visible_text)}\n      </w:r>\n    </w:p>"""\n\n\ndef _text_xml(text: str) -> str:\n    escaped = escape(text, quote=False)\n    preserve = \' xml:space="preserve"\' if text != text.strip() else ""\n    return f"<w:t{preserve}>{escaped}</w:t>"\n\n\ndef _styles_xml() -> str:\n    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:styles xmlns:w="{_WORD_NS}">\n  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">\n    <w:name w:val="Normal"/>\n  </w:style>\n  <w:style w:type="paragraph" w:styleId="Heading1">\n    <w:name w:val="heading 1"/>\n    <w:basedOn w:val="Normal"/>\n    <w:next w:val="Normal"/>\n    <w:pPr>\n      <w:outlineLvl w:val="0"/>\n    </w:pPr>\n    <w:rPr>\n      <w:b/>\n      <w:sz w:val="32"/>\n    </w:rPr>\n  </w:style>\n</w:styles>\n"""\n'
DOCX_SERVICE = 'from __future__ import annotations\n\nfrom dataclasses import dataclass\n\nfrom skills.docx import DocxEditPlan, DocxRewritePlan, apply_docx_edit_plan, apply_docx_rewrite_plan\n\nfrom backend.app.services.docx_service.builder import build_docx_package\n\n\n@dataclass(frozen=True)\nclass DocxTransformOutput:\n    content: str\n    artifact_content: bytes\n\n\n@dataclass\nclass DocxService:\n    """Service-layer wrapper around reusable DOCX skill logic and deterministic DOCX packaging."""\n\n    def apply_edit(self, document_text: str, *, target: str, replacement: str) -> str:\n        plan = DocxEditPlan(operation="replace", target=target, replacement=replacement)\n        return apply_docx_edit_plan(document_text, plan)\n\n    def transform_document(self, document_text: str, *, target: str, replacement: str) -> DocxTransformOutput:\n        plan = DocxRewritePlan(replacements=((target, replacement),), normalize_headings=True)\n        revised_content = apply_docx_rewrite_plan(document_text, plan)\n        artifact_payload = build_docx_package(revised_content)\n        return DocxTransformOutput(content=revised_content, artifact_content=artifact_payload)\n'
TEST_DOCX_PDF = 'from io import BytesIO\nfrom zipfile import ZipFile, is_zipfile\n\nfrom backend.app.services.docx_service import DocxService\nfrom backend.app.services.pdf_service import PdfService\n\n\ndef test_docx_service_wraps_skill_edit_logic_and_builds_valid_docx() -> None:\n    service = DocxService()\n\n    result = service.transform_document(\n        "# quarterly report\\nStatus: draft",\n        target="draft",\n        replacement="final",\n    )\n\n    assert result.content == "# Quarterly Report\\nStatus: final"\n    assert is_zipfile(BytesIO(result.artifact_content))\n\n    with ZipFile(BytesIO(result.artifact_content)) as docx:\n        names = set(docx.namelist())\n        assert "[Content_Types].xml" in names\n        assert "_rels/.rels" in names\n        assert "word/document.xml" in names\n        document_xml = docx.read("word/document.xml").decode("utf-8")\n\n    assert "Quarterly Report" in document_xml\n    assert "Status: final" in document_xml\n\n\ndef test_pdf_service_wraps_skill_summary_logic() -> None:\n    service = PdfService()\n\n    result = service.transform_pdf(\n        "First finding is stable. Second finding requires follow-up. Third finding is optional.",\n        max_sentences=2,\n    )\n\n    assert result.extracted_text == "First finding is stable. Second finding requires follow-up. Third finding is optional."\n    assert result.summary == "First finding is stable. Second finding requires follow-up."\n    assert b"PDF Summary Report" in result.artifact_content\n'
TEST_J1_API = 'from io import BytesIO\nfrom pathlib import Path\nfrom zipfile import ZipFile, is_zipfile\n\nimport pytest\nfrom fastapi.testclient import TestClient\n\nfrom backend.app.core.config import get_settings\nfrom backend.app.main import app\nfrom backend.app.repositories.sqlite import SqliteArtifactSourceRepository\n\nclient = TestClient(app)\n\n\ndef _reset_app_state() -> None:\n    for attribute in (\n        "app_container",\n        "g1_execution_coordinator",\n        "official_execution_coordinator",\n        "llm_provider",\n        "llm_text_service",\n    ):\n        if hasattr(app.state, attribute):\n            delattr(app.state, attribute)\n\n\ndef _configure_sqlite_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> str:\n    repository_db_path = str(tmp_path / "repositories.sqlite3")\n    monkeypatch.setenv("METADATA_BACKEND", "sqlite")\n    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")\n    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))\n    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))\n    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))\n    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))\n    monkeypatch.setenv("REPOSITORY_DB_PATH", repository_db_path)\n    get_settings.cache_clear()\n    _reset_app_state()\n    return repository_db_path\n\n\ndef test_j1_docx_edit_official_flow_returns_valid_docx_and_preserves_lineage(\n    monkeypatch: pytest.MonkeyPatch,\n    tmp_path: Path,\n) -> None:\n    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)\n\n    session_response = client.post("/sessions", json={})\n    assert session_response.status_code == 201\n    session_id = session_response.json()["id"]\n\n    upload_response = client.post(\n        "/uploads",\n        data={"session_id": session_id},\n        files={"file": ("draft.txt", b"# report\\nStatus: draft", "text/plain")},\n    )\n    assert upload_response.status_code == 201\n    upload_id = upload_response.json()["id"]\n\n    task_response = client.post(\n        "/tasks",\n        json={"session_id": session_id, "task_type": "docx_edit"},\n    )\n    assert task_response.status_code == 201\n    task_id = task_response.json()["id"]\n\n    execute_response = client.post(\n        f"/tasks/{task_id}/execute",\n        json={"uploaded_file_ids": [upload_id]},\n    )\n    assert execute_response.status_code == 200\n    payload = execute_response.json()\n    assert payload["status"] == "succeeded"\n    assert payload["result_data"]["task_type"] == "docx_edit"\n    assert payload["result_data"]["source_mode"] == "uploaded_source"\n    artifact_id = payload["result_data"]["artifact_ids"][0]\n\n    artifact_response = client.get(f"/artifacts/{artifact_id}")\n    assert artifact_response.status_code == 200\n    artifact = artifact_response.json()\n    assert artifact["filename"] == "edited.docx"\n    assert artifact["content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"\n    assert artifact["size_bytes"] > 0\n\n    download_response = client.get(f"/artifacts/{artifact_id}/download")\n    assert download_response.status_code == 200\n    docx_bytes = download_response.content\n    assert is_zipfile(BytesIO(docx_bytes))\n\n    with ZipFile(BytesIO(docx_bytes)) as docx:\n        names = set(docx.namelist())\n        assert "[Content_Types].xml" in names\n        assert "_rels/.rels" in names\n        assert "word/document.xml" in names\n        document_xml = docx.read("word/document.xml").decode("utf-8")\n\n    assert "Status: final" in document_xml\n\n    artifact_sources = SqliteArtifactSourceRepository(repository_db_path).list_by_artifact(artifact_id)\n    assert len(artifact_sources) == 1\n    assert artifact_sources[0].source_file_id == upload_id\n    assert artifact_sources[0].source_document_id is None\n    assert artifact_sources[0].source_presentation_id is None\n'


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"[PASS] wrote {rel}")


def main() -> None:
    if not (ROOT / "backend" / "app").exists():
        raise SystemExit("[FAIL] Put this script in repository root and run it from there.")

    write("backend/app/services/docx_service/builder.py", BUILDER)
    write("backend/app/services/docx_service/service.py", DOCX_SERVICE)

    route_text = read("backend/app/api/routes/tasks.py")
    route_text = route_text.replace(
        "_OFFICIAL_G1_SUPPORTED_TASK_TYPES = {TaskType.PDF_SUMMARY, TaskType.DATA_ANALYSIS}",
        "_OFFICIAL_G1_SUPPORTED_TASK_TYPES = {TaskType.PDF_SUMMARY, TaskType.DATA_ANALYSIS, TaskType.DOCX_EDIT}",
    )
    write("backend/app/api/routes/tasks.py", route_text)

    g1_text = read("backend/tests/api/test_g1_execution_flow.py")
    g1_text = g1_text.replace(
        '@pytest.mark.parametrize("task_type", ["docx_edit", "slides_generate"])',
        '@pytest.mark.parametrize("task_type", ["slides_generate"])',
    )
    write("backend/tests/api/test_g1_execution_flow.py", g1_text)

    write("backend/tests/services/test_docx_pdf_services.py", TEST_DOCX_PDF)

    coord_text = read("backend/tests/orchestrator/test_execution_coordinator.py")
    if "from io import BytesIO" not in coord_text:
        coord_text = coord_text.replace(
            "from pathlib import Path\n",
            "from io import BytesIO\nfrom pathlib import Path\nfrom zipfile import ZipFile, is_zipfile\n",
        )
    coord_text = coord_text.replace(
        """    if task_type is TaskType.DOCX_EDIT:\n        downloaded_artifact, downloaded_bytes = artifact_service.get_artifact_download(artifact.id)\n        assert downloaded_artifact.size_bytes > 0\n        assert downloaded_bytes.decode("utf-8") == expected_output\n""",
        """    if task_type is TaskType.DOCX_EDIT:\n        downloaded_artifact, downloaded_bytes = artifact_service.get_artifact_download(artifact.id)\n        assert downloaded_artifact.size_bytes > 0\n        assert is_zipfile(BytesIO(downloaded_bytes))\n        with ZipFile(BytesIO(downloaded_bytes)) as docx:\n            assert "word/document.xml" in set(docx.namelist())\n            document_xml = docx.read("word/document.xml").decode("utf-8")\n        assert expected_output in document_xml\n""",
    )
    write("backend/tests/orchestrator/test_execution_coordinator.py", coord_text)

    write("backend/tests/api/test_j1_docx_artifact_pipeline.py", TEST_J1_API)

    print("[DONE] J1 real DOCX artifact pipeline updates applied.")
    print("Run:")
    print("  python -m pytest -q")
    print("  python -m compileall backend")


if __name__ == "__main__":
    main()
