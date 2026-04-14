from io import BytesIO
from zipfile import ZipFile, is_zipfile

from backend.app.services.docx_service import DocxService
from backend.app.services.pdf_service import PdfService


def test_docx_service_wraps_skill_edit_logic_and_builds_valid_docx() -> None:
    service = DocxService()

    result = service.transform_document(
        "# quarterly report\nStatus: draft",
        target="draft",
        replacement="final",
    )

    assert result.content == "# Quarterly Report\nStatus: final"
    assert is_zipfile(BytesIO(result.artifact_content))

    with ZipFile(BytesIO(result.artifact_content)) as docx:
        names = set(docx.namelist())
        assert "[Content_Types].xml" in names
        assert "_rels/.rels" in names
        assert "word/document.xml" in names
        document_xml = docx.read("word/document.xml").decode("utf-8")

    assert "Quarterly Report" in document_xml
    assert "Status: final" in document_xml


def test_pdf_service_produces_honest_text_summary_report() -> None:
    service = PdfService()

    result = service.transform_pdf(
        "First finding is stable. Second finding requires follow-up. Third finding is optional.",
        max_sentences=2,
    )

    assert result.extracted_text == "First finding is stable. Second finding requires follow-up. Third finding is optional."
    assert result.summary == "First finding is stable. Second finding requires follow-up."
    assert result.artifact_content.startswith(b"Summary Report\n")
    assert b"Format: text/plain" in result.artifact_content
    assert b"not a PDF binary" in result.artifact_content
    assert not result.artifact_content.startswith(b"%PDF")
