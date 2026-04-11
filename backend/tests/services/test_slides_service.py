from backend.app.services.slides_service import SlidesService


def test_slides_service_generates_simple_pptx_payload() -> None:
    service = SlidesService()

    result = service.generate_deck("Intro slide. Problem statement. Proposed solution.")

    assert result.slide_count == 3
    assert result.summary_text == "Generated 3 slide(s)."
    assert result.artifact_content[:2] == b"PK"
