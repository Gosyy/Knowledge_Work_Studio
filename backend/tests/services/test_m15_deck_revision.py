from __future__ import annotations

from dataclasses import replace
from io import BytesIO
import zipfile

import pytest

from backend.app.domain import Presentation, PresentationVersion, StoredFile
from backend.app.services.slides_service import (
    DeckRevisionRequest,
    DeckRevisionScope,
    DeckRevisionService,
    StoryArcStage,
    build_presentation_plan,
)


class _MemoryStorage:
    backend_name = "memory"

    def __init__(self) -> None:
        self.items: dict[str, bytes] = {}

    def save_bytes(self, *, storage_key: str, content: bytes, content_type: str | None = None) -> str:
        self.items[storage_key] = content
        return f"memory://{storage_key}"

    def read_bytes(self, *, storage_key: str) -> bytes:
        return self.items[storage_key]

    def exists(self, *, storage_key: str) -> bool:
        return storage_key in self.items

    def delete(self, *, storage_key: str) -> None:
        self.items.pop(storage_key, None)

    def get_size(self, *, storage_key: str) -> int | None:
        item = self.items.get(storage_key)
        return len(item) if item is not None else None

    def make_uri(self, *, storage_key: str) -> str:
        return f"memory://{storage_key}"


class _StoredFiles:
    def __init__(self) -> None:
        self.items: dict[str, StoredFile] = {}

    def create(self, stored_file: StoredFile) -> StoredFile:
        self.items[stored_file.id] = stored_file
        return stored_file

    def get(self, stored_file_id: str) -> StoredFile | None:
        return self.items.get(stored_file_id)

    def list_by_session(self, session_id: str) -> list[StoredFile]:
        return [item for item in self.items.values() if item.session_id == session_id]


class _Presentations:
    def __init__(self, presentation: Presentation | None = None) -> None:
        self.items: dict[str, Presentation] = {}
        if presentation is not None:
            self.items[presentation.id] = presentation

    def create(self, presentation: Presentation) -> Presentation:
        self.items[presentation.id] = presentation
        return presentation

    def get(self, presentation_id: str) -> Presentation | None:
        return self.items.get(presentation_id)

    def list_by_session(self, session_id: str) -> list[Presentation]:
        return [item for item in self.items.values() if item.session_id == session_id]


class _PresentationVersions:
    def __init__(self, versions: tuple[PresentationVersion, ...] = ()) -> None:
        self.items: list[PresentationVersion] = list(versions)

    def create(self, presentation_version: PresentationVersion) -> PresentationVersion:
        self.items.append(presentation_version)
        return presentation_version

    def list_by_presentation(self, presentation_id: str) -> list[PresentationVersion]:
        return [item for item in self.items if item.presentation_id == presentation_id]


def _service_with_existing_deck() -> tuple[DeckRevisionService, _MemoryStorage, _StoredFiles, _Presentations, _PresentationVersions]:
    storage = _MemoryStorage()
    stored_files = _StoredFiles()
    presentation = Presentation(
        id="pres_m15",
        session_id="ses_m15",
        current_file_id="sf_initial",
        presentation_type="generated_deck",
        title="M15 deck",
    )
    presentations = _Presentations(presentation)
    versions = _PresentationVersions(
        (
            PresentationVersion(
                id="presver_initial",
                presentation_id="pres_m15",
                file_id="sf_initial",
                version_number=1,
                created_from_task_id="task_initial",
                parent_version_id=None,
                change_summary="Initial deck",
            ),
        )
    )
    service = DeckRevisionService(
        storage=storage,
        stored_files=stored_files,
        presentations=presentations,
        presentation_versions=versions,
    )
    return service, storage, stored_files, presentations, versions


def test_m15_regenerate_one_slide_preserves_template_and_unchanged_slides() -> None:
    service, storage, stored_files, presentations, versions = _service_with_existing_deck()
    plan = build_presentation_plan(
        "Opening. Context. Analysis point. Compare options. Timeline. Data signal. Conclusion.",
        min_slides=7,
        max_slides=7,
    )
    target_slide = next(slide for slide in plan.slides if slide.story_arc_stage is StoryArcStage.ANALYSIS)

    result = service.regenerate_slide(
        DeckRevisionRequest(
            presentation_id="pres_m15",
            plan=plan,
            template_id="business_clean",
            target_slide_id=target_slide.slide_id,
            instruction="Emphasize customer risk and shorten the recommendation.",
            task_id="task_revision",
            owner_user_id="alice",
        )
    )

    assert result.scope is DeckRevisionScope.SLIDE
    assert result.template_id == "business_clean"
    assert result.revised_slide_ids == (target_slide.slide_id,)
    assert result.version.version_number == 2
    assert result.version.parent_version_id == "presver_initial"
    assert result.previous_file_id == "sf_initial"
    assert result.stored_file.kind == "presentation_revision"
    assert result.stored_file.owner_user_id == "alice"
    assert result.stored_file.checksum_sha256 is not None
    assert storage.exists(storage_key=result.stored_file.storage_key)
    assert stored_files.get(result.stored_file.id) == result.stored_file
    assert presentations.get("pres_m15").current_file_id == result.stored_file.id
    assert versions.list_by_presentation("pres_m15")[-1] == result.version

    original_by_id = {slide.slide_id: slide for slide in plan.slides}
    revised_by_id = {slide.slide_id: slide for slide in result.revised_plan.slides}
    for slide_id, original_slide in original_by_id.items():
        if slide_id == target_slide.slide_id:
            assert revised_by_id[slide_id].title != original_slide.title
            assert revised_by_id[slide_id].bullets != original_slide.bullets
            assert "Revision instruction" in (revised_by_id[slide_id].speaker_notes or "")
        else:
            assert revised_by_id[slide_id] == original_slide

    with zipfile.ZipFile(BytesIO(result.artifact_content), "r") as pptx_zip:
        assert "ppt/slides/slide1.xml" in set(pptx_zip.namelist())


def test_m15_regenerate_section_updates_only_target_story_arc_stage() -> None:
    service, _, _, _, _ = _service_with_existing_deck()
    plan = build_presentation_plan(
        "Opening. Context. Analysis one. Recommendation one. Analysis two. Recommendation two. Conclusion.",
        min_slides=7,
        max_slides=7,
    )
    target_ids = tuple(slide.slide_id for slide in plan.slides if slide.story_arc_stage is StoryArcStage.ANALYSIS)

    result = service.regenerate_section(
        DeckRevisionRequest(
            presentation_id="pres_m15",
            plan=plan,
            target_stage=StoryArcStage.ANALYSIS,
            instruction="Reframe this section around implementation risk.",
            change_summary="Refresh analysis section",
        )
    )

    assert result.scope is DeckRevisionScope.SECTION
    assert result.revised_slide_ids == target_ids
    assert result.version.change_summary == "Refresh analysis section"

    original_by_id = {slide.slide_id: slide for slide in plan.slides}
    revised_by_id = {slide.slide_id: slide for slide in result.revised_plan.slides}
    for slide_id, original_slide in original_by_id.items():
        if slide_id in target_ids:
            assert revised_by_id[slide_id] != original_slide
        else:
            assert revised_by_id[slide_id] == original_slide


def test_m15_revision_lineage_is_inspectable_and_ordered() -> None:
    service, _, _, _, _ = _service_with_existing_deck()
    plan = build_presentation_plan("Opening. Context. Analysis. Compare. Timeline. Data. Close.", min_slides=7, max_slides=7)

    first = service.regenerate_slide(
        DeckRevisionRequest(
            presentation_id="pres_m15",
            plan=plan,
            target_slide_index=2,
            instruction="First revision.",
        )
    )
    second = service.regenerate_slide(
        DeckRevisionRequest(
            presentation_id="pres_m15",
            plan=first.revised_plan,
            target_slide_index=2,
            instruction="Second revision.",
        )
    )

    lineage = service.list_revision_lineage("pres_m15")

    assert [version.version_number for version in lineage] == [1, 2, 3]
    assert lineage[-1].id == second.version.id
    assert second.version.parent_version_id == first.version.id


def test_m15_revision_fails_honestly_for_missing_presentation_or_target() -> None:
    storage = _MemoryStorage()
    service = DeckRevisionService(
        storage=storage,
        stored_files=_StoredFiles(),
        presentations=_Presentations(),
        presentation_versions=_PresentationVersions(),
    )
    plan = build_presentation_plan("Opening. Context. Analysis. Close.")

    with pytest.raises(ValueError, match="not found"):
        service.regenerate_slide(
            DeckRevisionRequest(
                presentation_id="missing",
                plan=plan,
                target_slide_index=0,
                instruction="Revise.",
            )
        )

    service, _, _, _, _ = _service_with_existing_deck()
    with pytest.raises(ValueError, match="out of range"):
        service.regenerate_slide(
            DeckRevisionRequest(
                presentation_id="pres_m15",
                plan=plan,
                target_slide_index=999,
                instruction="Revise.",
            )
        )


def test_m15_revision_requires_current_file_id() -> None:
    presentation = Presentation(
        id="pres_empty",
        session_id="ses_m15",
        current_file_id=None,
        presentation_type="generated_deck",
        title="Empty deck",
    )
    service = DeckRevisionService(
        storage=_MemoryStorage(),
        stored_files=_StoredFiles(),
        presentations=_Presentations(presentation),
        presentation_versions=_PresentationVersions(),
    )
    plan = build_presentation_plan("Opening. Context. Analysis. Close.")

    with pytest.raises(ValueError, match="no current_file_id"):
        service.regenerate_slide(
            DeckRevisionRequest(
                presentation_id="pres_empty",
                plan=plan,
                target_slide_index=0,
                instruction="Revise.",
            )
        )
