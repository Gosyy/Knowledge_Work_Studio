from __future__ import annotations

from dataclasses import dataclass, replace
from io import BytesIO
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest

from backend.app.domain import Presentation, PresentationVersion, StoredFile
from backend.app.services.slides_service import (
    DeckRevisionRequest,
    DeckRevisionService,
    ImageFitMode,
    PlannedSlide,
    PresentationPlan,
    SlideMediaAsset,
    SlideOutlineItem,
    SlideType,
    StoryArcStage,
    build_presentation_plan,
    build_source_grounded_plan,
    generate_pptx_from_outline,
    generate_pptx_from_plan,
)


_PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\x8d\xf5\x1d"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


@dataclass(frozen=True)
class SampleDeck:
    name: str
    payload: bytes
    expected_markers: tuple[str, ...] = ()


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
    def __init__(self, presentation: Presentation) -> None:
        self.items = {presentation.id: presentation}

    def create(self, presentation: Presentation) -> Presentation:
        self.items[presentation.id] = presentation
        return presentation

    def get(self, presentation_id: str) -> Presentation | None:
        return self.items.get(presentation_id)

    def list_by_session(self, session_id: str) -> list[Presentation]:
        return [item for item in self.items.values() if item.session_id == session_id]


class _PresentationVersions:
    def __init__(self) -> None:
        self.items = [
            PresentationVersion(
                id="presver_n5_initial",
                presentation_id="pres_n5",
                file_id="sf_n5_initial",
                version_number=1,
                created_from_task_id="task_n5_initial",
                parent_version_id=None,
                change_summary="Initial sample deck",
            )
        ]

    def create(self, presentation_version: PresentationVersion) -> PresentationVersion:
        self.items.append(presentation_version)
        return presentation_version

    def list_by_presentation(self, presentation_id: str) -> list[PresentationVersion]:
        return [item for item in self.items if item.presentation_id == presentation_id]


def _text_only_sample() -> SampleDeck:
    payload = generate_pptx_from_outline(
        (
            SlideOutlineItem(title="N5 text-only sample", bullets=("Opening", "Purpose")),
            SlideOutlineItem(title="Content", bullets=("One", "Two")),
            SlideOutlineItem(title="Close", bullets=("Decision", "Next step")),
        )
    )
    return SampleDeck(name="text_only", payload=payload, expected_markers=("N5 text-only sample",))


def _layout_template_sample() -> SampleDeck:
    plan = build_presentation_plan(
        "Executive opening. Market context. Analysis. Recommendation. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )
    payload = generate_pptx_from_plan(plan, template_id="business_clean")
    return SampleDeck(name="layout_template", payload=payload, expected_markers=("Executive opening",))


def _media_image_sample() -> SampleDeck:
    slide = PlannedSlide(
        slide_id="media_001",
        slide_type=SlideType.CONTENT,
        story_arc_stage=StoryArcStage.ANALYSIS,
        title="N5 media sample",
        bullets=("Image is embedded as real PPT media.",),
        layout_hint="content_with_visual",
        media_assets=(
            SlideMediaAsset(
                media_id="img_n5",
                filename="n5_sample.png",
                content_type="image/png",
                data=_PNG_1X1,
                width_px=1,
                height_px=1,
                fit_mode=ImageFitMode.CONTAIN,
                alt_text="N5 sample image",
                caption="N5 image caption",
                source_label="deterministic test asset",
            ),
        ),
    )
    plan = PresentationPlan(
        deck_title="N5 media sample",
        deck_goal="Validate media export.",
        audience="test",
        tone="clear",
        target_slide_count=1,
        story_arc=(slide.story_arc_stage,),
        slides=(slide,),
    )
    payload = generate_pptx_from_plan(plan, template_id="default_light")
    return SampleDeck(name="media_image", payload=payload, expected_markers=("N5 media sample", "N5 image caption"))


def _structured_blocks_sample() -> SampleDeck:
    plan = build_presentation_plan(
        "Executive opening. Market context. Operating model. Compare options. Delivery timeline. Revenue 10 cost 4 margin 6. Final recommendation.",
        min_slides=7,
        max_slides=7,
    )
    payload = generate_pptx_from_plan(plan, template_id="default_light")
    return SampleDeck(
        name="structured_blocks",
        payload=payload,
        expected_markers=("table_block cell", "chart_block bar", "business_metric_block card"),
    )


def _source_grounded_sample() -> SampleDeck:
    plan = build_presentation_plan(
        "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )
    grounded = build_source_grounded_plan(
        plan,
        source_text="Alpha source evidence. Beta source evidence. Gamma source evidence.",
        source_refs=(
            {
                "kind": "stored_file",
                "source_id": "sf_n5_source",
                "role": "primary_source",
                "source_file_id": "sf_n5_source",
                "derived_content_id": "dcon_n5_source",
            },
        ),
    )
    payload = generate_pptx_from_plan(grounded.plan, template_id="default_light")
    return SampleDeck(name="source_grounded", payload=payload, expected_markers=("Source:", "stored_file/sf_n5_source"))


def _revised_sample() -> SampleDeck:
    presentation = Presentation(
        id="pres_n5",
        session_id="ses_n5",
        current_file_id="sf_n5_initial",
        presentation_type="generated_deck",
        title="N5 revised deck",
    )
    service = DeckRevisionService(
        storage=_MemoryStorage(),
        stored_files=_StoredFiles(),
        presentations=_Presentations(presentation),
        presentation_versions=_PresentationVersions(),
    )
    plan = build_presentation_plan(
        "Opening. Context. Analysis. Compare. Timeline. Data. Close.",
        min_slides=7,
        max_slides=7,
    )
    result = service.regenerate_slide(
        DeckRevisionRequest(
            presentation_id="pres_n5",
            plan=plan,
            target_slide_index=2,
            instruction="Revise this sample slide for visual smoke validation.",
            task_id="task_n5_revision",
            owner_user_id="alice",
        )
    )
    return SampleDeck(name="revised", payload=result.artifact_content, expected_markers=("revised:",))


def _sample_decks() -> tuple[SampleDeck, ...]:
    return (
        _text_only_sample(),
        _layout_template_sample(),
        _media_image_sample(),
        _structured_blocks_sample(),
        _source_grounded_sample(),
        _revised_sample(),
    )


def _assert_valid_pptx(sample: SampleDeck) -> None:
    assert sample.payload.startswith(b"PK")
    with zipfile.ZipFile(BytesIO(sample.payload), "r") as pptx_zip:
        names = set(pptx_zip.namelist())
        assert "[Content_Types].xml" in names
        assert "ppt/presentation.xml" in names
        assert "ppt/slides/slide1.xml" in names
        assert "ppt/theme/theme1.xml" in names

        slide_names = sorted(name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml"))
        assert slide_names

        all_xml = "\n".join(
            pptx_zip.read(name).decode("utf-8", errors="replace")
            for name in names
            if name.endswith(".xml")
        )
        for marker in sample.expected_markers:
            assert marker in all_xml

        if sample.name == "media_image":
            assert any(name.startswith("ppt/media/") and name.endswith(".png") for name in names)


def test_n5_sample_decks_export_as_valid_pptx_packages() -> None:
    samples = _sample_decks()

    assert {sample.name for sample in samples} == {
        "text_only",
        "layout_template",
        "media_image",
        "structured_blocks",
        "source_grounded",
        "revised",
    }

    for sample in samples:
        _assert_valid_pptx(sample)


def test_n5_sample_deck_export_is_deterministic_for_non_revision_samples() -> None:
    first = {
        sample.name: sample.payload
        for sample in _sample_decks()
        if sample.name != "revised"
    }
    second = {
        sample.name: sample.payload
        for sample in _sample_decks()
        if sample.name != "revised"
    }

    assert first.keys() == second.keys()
    for name in first:
        assert first[name] == second[name]


def test_n5_sample_deck_zip_metadata_is_deterministic() -> None:
    sample = _media_image_sample()

    with zipfile.ZipFile(BytesIO(sample.payload), "r") as pptx_zip:
        infos = pptx_zip.infolist()

    assert infos
    assert {info.date_time for info in infos} == {(1980, 1, 1, 0, 0, 0)}
    assert {info.compress_type for info in infos} == {zipfile.ZIP_DEFLATED}


def test_n5_optional_libreoffice_visual_smoke(tmp_path: Path) -> None:
    office_binary = shutil.which("soffice") or shutil.which("libreoffice")
    if office_binary is None:
        pytest.skip("LibreOffice/soffice is not installed; optional visual smoke skipped honestly.")

    sample = _structured_blocks_sample()
    input_path = tmp_path / f"{sample.name}.pptx"
    output_dir = tmp_path / "converted"
    output_dir.mkdir()
    input_path.write_bytes(sample.payload)

    result = subprocess.run(
        [
            office_binary,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(input_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    output_pdf = output_dir / f"{sample.name}.pdf"
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 0
