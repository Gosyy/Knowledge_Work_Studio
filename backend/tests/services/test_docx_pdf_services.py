from backend.app.services.docx_service import DocxService
from backend.app.services.pdf_service import PdfService


def test_docx_service_wraps_skill_edit_logic() -> None:
    service = DocxService()

    result = service.transform_document(
        "# quarterly report\nStatus: draft",
        target="draft",
        replacement="final",
    )

    assert result.content == "# Quarterly Report\nStatus: final"
    assert result.artifact_content == b"# Quarterly Report\nStatus: final"


def test_pdf_service_wraps_skill_summary_logic() -> None:
    service = PdfService()

    summary = service.summarize(
        "First finding is stable. Second finding requires follow-up. Third finding is optional.",
        max_sentences=2,
    )

    assert summary == "First finding is stable. Second finding requires follow-up."
