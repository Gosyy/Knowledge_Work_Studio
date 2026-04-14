from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

PDF_SERVICE = 'from __future__ import annotations\n\nfrom dataclasses import dataclass\n\nfrom skills.pdf import extract_pdf_text, summarize_pdf_text\n\n\n@dataclass(frozen=True)\nclass PdfTransformOutput:\n    extracted_text: str\n    summary: str\n    artifact_content: bytes\n\n\n@dataclass\nclass PdfService:\n    """Service-layer wrapper for honest text report output from PDF/source content.\n\n    J2 deliberately produces a text report artifact, not a PDF binary. The\n    orchestrator labels this output as summary.txt / text/plain, so artifact\n    metadata matches the actual bytes.\n    """\n\n    def summarize(self, text: str, *, max_sentences: int = 2) -> str:\n        return summarize_pdf_text(text, max_sentences=max_sentences)\n\n    def transform_pdf(self, content: str | bytes, *, max_sentences: int = 2) -> PdfTransformOutput:\n        extraction = extract_pdf_text(content)\n        summary = summarize_pdf_text(extraction.extracted_text, max_sentences=max_sentences)\n        artifact_content = self._render_text_summary_report(\n            extracted_text=extraction.extracted_text,\n            summary=summary,\n        )\n        return PdfTransformOutput(\n            extracted_text=extraction.extracted_text,\n            summary=summary,\n            artifact_content=artifact_content,\n        )\n\n    @staticmethod\n    def _render_text_summary_report(*, extracted_text: str, summary: str) -> bytes:\n        report = (\n            "Summary Report\\n"\n            "==============\\n\\n"\n            "Format: text/plain\\n"\n            "This artifact is an honest text report, not a PDF binary.\\n\\n"\n            "Summary\\n"\n            "-------\\n"\n            f"{summary}\\n\\n"\n            "Extracted Text\\n"\n            "--------------\\n"\n            f"{extracted_text}\\n"\n        )\n        return report.encode("utf-8")\n'
TEST_DOCX_PDF = 'from io import BytesIO\nfrom zipfile import ZipFile, is_zipfile\n\nfrom backend.app.services.docx_service import DocxService\nfrom backend.app.services.pdf_service import PdfService\n\n\ndef test_docx_service_wraps_skill_edit_logic_and_builds_valid_docx() -> None:\n    service = DocxService()\n\n    result = service.transform_document(\n        "# quarterly report\\nStatus: draft",\n        target="draft",\n        replacement="final",\n    )\n\n    assert result.content == "# Quarterly Report\\nStatus: final"\n    assert is_zipfile(BytesIO(result.artifact_content))\n\n    with ZipFile(BytesIO(result.artifact_content)) as docx:\n        names = set(docx.namelist())\n        assert "[Content_Types].xml" in names\n        assert "_rels/.rels" in names\n        assert "word/document.xml" in names\n        document_xml = docx.read("word/document.xml").decode("utf-8")\n\n    assert "Quarterly Report" in document_xml\n    assert "Status: final" in document_xml\n\n\ndef test_pdf_service_produces_honest_text_summary_report() -> None:\n    service = PdfService()\n\n    result = service.transform_pdf(\n        "First finding is stable. Second finding requires follow-up. Third finding is optional.",\n        max_sentences=2,\n    )\n\n    assert result.extracted_text == "First finding is stable. Second finding requires follow-up. Third finding is optional."\n    assert result.summary == "First finding is stable. Second finding requires follow-up."\n    assert result.artifact_content.startswith(b"Summary Report\\n")\n    assert b"Format: text/plain" in result.artifact_content\n    assert b"not a PDF binary" in result.artifact_content\n    assert not result.artifact_content.startswith(b"%PDF")\n'
TEST_J2_API = 'from pathlib import Path\n\nimport pytest\nfrom fastapi.testclient import TestClient\n\nfrom backend.app.core.config import get_settings\nfrom backend.app.main import app\nfrom backend.app.repositories.sqlite import SqliteArtifactSourceRepository\n\nclient = TestClient(app)\n\n\ndef _reset_app_state() -> None:\n    for attribute in (\n        "app_container",\n        "g1_execution_coordinator",\n        "official_execution_coordinator",\n        "llm_provider",\n        "llm_text_service",\n    ):\n        if hasattr(app.state, attribute):\n            delattr(app.state, attribute)\n\n\ndef _configure_sqlite_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> str:\n    repository_db_path = str(tmp_path / "repositories.sqlite3")\n    monkeypatch.setenv("METADATA_BACKEND", "sqlite")\n    monkeypatch.setenv("SQLITE_RUNTIME_ALLOWED", "true")\n    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))\n    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))\n    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))\n    monkeypatch.setenv("TEMP_DIR", str(tmp_path / "temp"))\n    monkeypatch.setenv("REPOSITORY_DB_PATH", repository_db_path)\n    get_settings.cache_clear()\n    _reset_app_state()\n    return repository_db_path\n\n\ndef test_j2_pdf_summary_official_flow_returns_honest_text_report_and_preserves_lineage(\n    monkeypatch: pytest.MonkeyPatch,\n    tmp_path: Path,\n) -> None:\n    repository_db_path = _configure_sqlite_test_env(monkeypatch, tmp_path)\n\n    session_response = client.post("/sessions", json={})\n    assert session_response.status_code == 201\n    session_id = session_response.json()["id"]\n\n    upload_response = client.post(\n        "/uploads",\n        data={"session_id": session_id},\n        files={\n            "file": (\n                "source.txt",\n                b"First finding is stable. Second finding requires follow-up. Third finding is optional.",\n                "text/plain",\n            )\n        },\n    )\n    assert upload_response.status_code == 201\n    upload_id = upload_response.json()["id"]\n\n    task_response = client.post(\n        "/tasks",\n        json={"session_id": session_id, "task_type": "pdf_summary"},\n    )\n    assert task_response.status_code == 201\n    task_id = task_response.json()["id"]\n\n    execute_response = client.post(\n        f"/tasks/{task_id}/execute",\n        json={"uploaded_file_ids": [upload_id]},\n    )\n    assert execute_response.status_code == 200\n    payload = execute_response.json()\n    assert payload["status"] == "succeeded"\n    assert payload["result_data"]["task_type"] == "pdf_summary"\n    assert payload["result_data"]["source_mode"] == "uploaded_source"\n    artifact_id = payload["result_data"]["artifact_ids"][0]\n\n    artifact_response = client.get(f"/artifacts/{artifact_id}")\n    assert artifact_response.status_code == 200\n    artifact = artifact_response.json()\n    assert artifact["filename"] == "summary.txt"\n    assert artifact["content_type"] == "text/plain"\n    assert artifact["size_bytes"] > 0\n\n    download_response = client.get(f"/artifacts/{artifact_id}/download")\n    assert download_response.status_code == 200\n    assert download_response.headers["content-type"] == "text/plain; charset=utf-8"\n    report_bytes = download_response.content\n    assert report_bytes.startswith(b"Summary Report\\n")\n    assert b"Format: text/plain" in report_bytes\n    assert b"not a PDF binary" in report_bytes\n    assert not report_bytes.startswith(b"%PDF")\n\n    artifact_sources = SqliteArtifactSourceRepository(repository_db_path).list_by_artifact(artifact_id)\n    assert len(artifact_sources) == 1\n    assert artifact_sources[0].source_file_id == upload_id\n    assert artifact_sources[0].source_document_id is None\n    assert artifact_sources[0].source_presentation_id is None\n'


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

    write("backend/app/services/pdf_service/service.py", PDF_SERVICE)
    write("backend/tests/services/test_docx_pdf_services.py", TEST_DOCX_PDF)

    coord_path = "backend/tests/orchestrator/test_execution_coordinator.py"
    coord_text = read(coord_path)
    coord_text = coord_text.replace(
        '        assert b"PDF Summary Report" in downloaded_bytes\n        assert expected_output.encode("utf-8") in downloaded_bytes\n',
        '        assert downloaded_bytes.startswith(b"Summary Report\\n")\n        assert b"Format: text/plain" in downloaded_bytes\n        assert b"not a PDF binary" in downloaded_bytes\n        assert not downloaded_bytes.startswith(b"%PDF")\n        assert expected_output.encode("utf-8") in downloaded_bytes\n',
    )
    write(coord_path, coord_text)

    g1_path = "backend/tests/api/test_g1_execution_flow.py"
    g1_text = read(g1_path)
    g1_text = g1_text.replace(
        '    assert b"Alpha. Beta." in download_response.content\n',
        '    assert download_response.content.startswith(b"Summary Report\\n")\n    assert b"Format: text/plain" in download_response.content\n    assert b"not a PDF binary" in download_response.content\n    assert b"Alpha. Beta." in download_response.content\n',
    )
    write(g1_path, g1_text)

    write("backend/tests/api/test_j2_honest_pdf_report_pipeline.py", TEST_J2_API)

    print("[DONE] J2 honest PDF/report pipeline updates applied.")
    print("Run:")
    print("  python -m pytest -q")
    print("  python -m compileall backend")


if __name__ == "__main__":
    main()
