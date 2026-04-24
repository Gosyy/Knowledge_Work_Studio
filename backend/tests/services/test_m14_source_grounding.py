from io import BytesIO
import zipfile

from backend.app.domain import DerivedContent, StoredFile
from backend.app.services.slides_service import SlidesService
from backend.app.services.slides_service.generator import generate_pptx_from_plan
from backend.app.services.slides_service.outline import build_presentation_plan
from backend.app.services.task_source_service import TaskSourceService


class _StoredFiles:
    def __init__(self, stored_file: StoredFile) -> None:
        self.stored_file = stored_file

    def get(self, stored_file_id: str) -> StoredFile | None:
        return self.stored_file if stored_file_id == self.stored_file.id else None


class _DerivedContents:
    def __init__(self, item: DerivedContent) -> None:
        self.item = item
        self.created: list[DerivedContent] = []

    def list_by_file(self, file_id: str) -> list[DerivedContent]:
        return [self.item] if file_id == self.item.file_id else []

    def create(self, derived_content: DerivedContent) -> DerivedContent:
        self.created.append(derived_content)
        return derived_content


class _UnusedRepository:
    def get(self, item_id: str):
        return None

    def create(self, item):
        return item


class _UnusedArtifactSources:
    def create(self, item):
        return item


class _FailingStorage:
    backend_name = "local"

    def read_bytes(self, *, storage_key: str) -> bytes:
        raise AssertionError("storage should not be read when derived_contents cache is available")


def test_m14_task_source_service_exposes_cached_derived_content_for_grounding() -> None:
    stored_file = StoredFile(
        id="sf_cached",
        session_id="ses_m14",
        task_id=None,
        kind="uploaded_source",
        file_type="txt",
        mime_type="text/plain",
        title="Cached source",
        original_filename="source.txt",
        storage_backend="local",
        storage_key="stored/sf_cached.txt",
        storage_uri="local://stored/sf_cached.txt",
        checksum_sha256=None,
        size_bytes=12,
        owner_user_id="alice",
    )
    cached = DerivedContent(
        id="dcon_cached",
        file_id="sf_cached",
        content_kind="extracted_text",
        text_content="Alpha source. Beta source.",
        structured_json=None,
        outline_json=None,
        language=None,
    )
    derived_contents = _DerivedContents(cached)
    service = TaskSourceService(
        uploads=_UnusedRepository(),
        stored_files=_StoredFiles(stored_file),
        documents=_UnusedRepository(),
        presentations=_UnusedRepository(),
        artifact_sources=_UnusedArtifactSources(),
        derived_contents=derived_contents,
        storage=_FailingStorage(),
    )

    resolved = service.build_execution_input(
        session_id="ses_m14",
        owner_user_id="alice",
        prompt_content=None,
        uploaded_file_ids=[],
        stored_file_ids=["sf_cached"],
        document_ids=[],
        presentation_ids=[],
    )

    assert resolved.content == "Alpha source. Beta source."
    assert derived_contents.created == []
    assert resolved.as_result_refs() == [
        {"kind": "stored_file", "source_id": "sf_cached", "role": "primary_source"}
    ]
    assert resolved.as_grounding_refs() == (
        {
            "kind": "stored_file",
            "source_id": "sf_cached",
            "role": "primary_source",
            "source_file_id": "sf_cached",
            "derived_content_id": "dcon_cached",
        },
    )


def test_m14_slides_service_attaches_source_citations_and_metadata() -> None:
    service = SlidesService()

    result = service.generate_deck(
        "Alpha source. Beta source. Gamma recommendation.",
        source_refs=(
            {
                "kind": "stored_file",
                "source_id": "sf_m14",
                "role": "primary_source",
                "source_file_id": "sf_m14",
                "derived_content_id": "dcon_m14",
            },
        ),
    )

    assert result.source_grounding_metadata is not None
    assert result.source_grounding_metadata["citation_count"] == result.slide_count
    assert result.plan.slides[0].citations
    assert result.plan.slides[0].source_notes
    assert result.plan.slides[0].citations[0].derived_content_id == "dcon_m14"

    with zipfile.ZipFile(BytesIO(result.artifact_content), "r") as pptx_zip:
        first_slide_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")

    assert "source_citation" in first_slide_xml
    assert "Source: stored_file/sf_m14" in first_slide_xml


def test_m14_prompt_only_slides_have_no_source_citations() -> None:
    service = SlidesService()

    result = service.generate_deck("Prompt only. No sources. Final recommendation.")

    assert result.source_grounding_metadata == {"citation_count": 0, "citations": []}
    assert all(not slide.citations for slide in result.plan.slides)


def test_m14_grounded_plan_can_render_directly_to_valid_pptx() -> None:
    plan = build_presentation_plan("Alpha source. Beta source. Gamma recommendation.")
    result = service_result = SlidesService().generate_deck(
        "Alpha source. Beta source. Gamma recommendation.",
        source_refs=(
            {
                "kind": "document",
                "source_id": "doc_m14",
                "role": "primary_source",
                "source_document_id": "doc_m14",
                "derived_content_id": "dcon_doc_m14",
            },
        ),
    )

    payload = generate_pptx_from_plan(result.plan, template_id="default_light")
    assert payload[:2] == b"PK"

    with zipfile.ZipFile(BytesIO(payload), "r") as pptx_zip:
        names = set(pptx_zip.namelist())
        first_slide_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")

    assert "ppt/slides/slide1.xml" in names
    assert "Source: document/doc_m14" in first_slide_xml
    assert service_result.source_grounding_metadata["citation_count"] == len(plan.slides)
