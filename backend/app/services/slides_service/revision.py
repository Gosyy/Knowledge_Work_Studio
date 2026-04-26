from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from uuid import uuid4

from backend.app.domain import Presentation, PresentationVersion, StoredFile
from backend.app.repositories import (
    FileStorage,
    PresentationRepository,
    PresentationVersionRepository,
    StoredFileRepository,
)
from backend.app.services.slides_service.generator import generate_pptx_from_plan
from backend.app.services.slides_service.outline import PlannedSlide, PresentationPlan, StoryArcStage
from backend.app.services.slides_service.revision_strategy import DeterministicRevisionStrategy, SlideRevisionStrategy


_PPTX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


class DeckRevisionScope(str, Enum):
    SLIDE = "slide"
    SECTION = "section"


@dataclass(frozen=True)
class SlideRevisionDelta:
    slide_id: str
    old_title: str
    new_title: str
    old_bullets: tuple[str, ...]
    new_bullets: tuple[str, ...]


@dataclass(frozen=True)
class DeckRevisionRequest:
    presentation_id: str
    plan: PresentationPlan
    instruction: str
    template_id: str = "default_light"
    task_id: str | None = None
    owner_user_id: str = "user_local_default"
    target_slide_id: str | None = None
    target_slide_index: int | None = None
    target_stage: StoryArcStage | str | None = None
    change_summary: str | None = None


@dataclass(frozen=True)
class DeckRevisionResult:
    presentation: Presentation
    version: PresentationVersion
    stored_file: StoredFile
    revised_plan: PresentationPlan
    template_id: str
    scope: DeckRevisionScope
    revised_slide_ids: tuple[str, ...]
    deltas: tuple[SlideRevisionDelta, ...]
    artifact_content: bytes
    previous_version_id: str | None
    previous_file_id: str | None


@dataclass(frozen=True)
class DeckRestoreRequest:
    presentation_id: str
    target_version_id: str
    owner_user_id: str = "user_local_default"
    task_id: str | None = None
    change_summary: str | None = None


@dataclass(frozen=True)
class DeckRestoreResult:
    presentation: Presentation
    version: PresentationVersion
    target_version: PresentationVersion
    previous_version_id: str | None
    previous_file_id: str | None


@dataclass
class DeckRevisionService:
    storage: FileStorage
    stored_files: StoredFileRepository
    presentations: PresentationRepository
    presentation_versions: PresentationVersionRepository
    revision_strategy: SlideRevisionStrategy = field(default_factory=DeterministicRevisionStrategy)

    def regenerate_slide(self, request: DeckRevisionRequest) -> DeckRevisionResult:
        presentation = self._require_presentation(request.presentation_id)
        target_index = self._resolve_target_slide_index(request.plan, request)
        old_slide = request.plan.slides[target_index]
        new_slide = self.revision_strategy.revise_slide(
            old_slide,
            instruction=request.instruction,
            task_id=request.task_id,
        )

        slides = list(request.plan.slides)
        slides[target_index] = new_slide
        revised_plan = replace(request.plan, slides=tuple(slides))

        delta = _build_delta(old_slide, new_slide)
        return self._persist_revision(
            request=request,
            presentation=presentation,
            revised_plan=revised_plan,
            scope=DeckRevisionScope.SLIDE,
            revised_slide_ids=(new_slide.slide_id,),
            deltas=(delta,),
        )

    def regenerate_section(self, request: DeckRevisionRequest) -> DeckRevisionResult:
        presentation = self._require_presentation(request.presentation_id)
        target_stage = self._resolve_target_stage(request)

        slides: list[PlannedSlide] = []
        revised_slide_ids: list[str] = []
        deltas: list[SlideRevisionDelta] = []
        for slide in request.plan.slides:
            if slide.story_arc_stage is target_stage:
                revised_slide = self.revision_strategy.revise_slide(
                    slide,
                    instruction=request.instruction,
                    task_id=request.task_id,
                )
                slides.append(revised_slide)
                revised_slide_ids.append(revised_slide.slide_id)
                deltas.append(_build_delta(slide, revised_slide))
            else:
                slides.append(slide)

        if not revised_slide_ids:
            raise ValueError(f"No slides found for revision stage: {target_stage.value}")

        revised_plan = replace(request.plan, slides=tuple(slides))
        return self._persist_revision(
            request=request,
            presentation=presentation,
            revised_plan=revised_plan,
            scope=DeckRevisionScope.SECTION,
            revised_slide_ids=tuple(revised_slide_ids),
            deltas=tuple(deltas),
        )

    def list_revision_lineage(self, presentation_id: str) -> tuple[PresentationVersion, ...]:
        return tuple(
            sorted(
                self.presentation_versions.list_by_presentation(presentation_id),
                key=lambda version: version.version_number,
            )
        )

    def restore_version(self, request: DeckRestoreRequest) -> DeckRestoreResult:
        presentation = self._require_presentation(request.presentation_id)
        versions = self.list_revision_lineage(presentation.id)
        target_version = next((version for version in versions if version.id == request.target_version_id), None)
        if target_version is None:
            raise ValueError(
                f"Presentation version '{request.target_version_id}' not found for presentation '{presentation.id}'."
            )

        previous_version = versions[-1] if versions else None
        if previous_version is not None and previous_version.id == target_version.id:
            raise ValueError(f"Presentation version '{target_version.id}' is already current.")

        next_version_number = (previous_version.version_number + 1) if previous_version else 1
        restored_version = PresentationVersion(
            id=f"presver_restore_{uuid4().hex}",
            presentation_id=presentation.id,
            file_id=target_version.file_id,
            version_number=next_version_number,
            created_from_task_id=request.task_id,
            parent_version_id=previous_version.id if previous_version else None,
            change_summary=request.change_summary
            or f"Restore to version {target_version.version_number}",
        )
        self.presentation_versions.create(restored_version)

        updated_presentation = replace(
            presentation,
            current_file_id=target_version.file_id,
            updated_at=datetime.now(timezone.utc),
        )
        self.presentations.create(updated_presentation)

        return DeckRestoreResult(
            presentation=updated_presentation,
            version=restored_version,
            target_version=target_version,
            previous_version_id=previous_version.id if previous_version else None,
            previous_file_id=presentation.current_file_id,
        )

    def _require_presentation(self, presentation_id: str) -> Presentation:
        presentation = self.presentations.get(presentation_id)
        if presentation is None:
            raise ValueError(f"Presentation '{presentation_id}' not found.")
        if presentation.current_file_id is None:
            raise ValueError(f"Presentation '{presentation_id}' has no current_file_id to revise.")
        return presentation

    def _resolve_target_slide_index(self, plan: PresentationPlan, request: DeckRevisionRequest) -> int:
        if request.target_slide_id is not None:
            for index, slide in enumerate(plan.slides):
                if slide.slide_id == request.target_slide_id:
                    return index
            raise ValueError(f"Slide '{request.target_slide_id}' not found in presentation plan.")

        if request.target_slide_index is not None:
            if request.target_slide_index < 0 or request.target_slide_index >= len(plan.slides):
                raise ValueError(f"Slide index {request.target_slide_index} is out of range.")
            return request.target_slide_index

        raise ValueError("Slide revision requires target_slide_id or target_slide_index.")

    def _resolve_target_stage(self, request: DeckRevisionRequest) -> StoryArcStage:
        if request.target_stage is None:
            raise ValueError("Section revision requires target_stage.")
        if isinstance(request.target_stage, StoryArcStage):
            return request.target_stage
        try:
            return StoryArcStage(str(request.target_stage))
        except ValueError as exc:
            raise ValueError(f"Unsupported story arc stage for section revision: {request.target_stage}") from exc

    def _persist_revision(
        self,
        *,
        request: DeckRevisionRequest,
        presentation: Presentation,
        revised_plan: PresentationPlan,
        scope: DeckRevisionScope,
        revised_slide_ids: tuple[str, ...],
        deltas: tuple[SlideRevisionDelta, ...],
    ) -> DeckRevisionResult:
        artifact_content = generate_pptx_from_plan(revised_plan, template_id=request.template_id)
        previous_versions = self.list_revision_lineage(presentation.id)
        previous_version = previous_versions[-1] if previous_versions else None
        next_version_number = (previous_version.version_number + 1) if previous_version else 1

        stored_file_id = f"sf_presrev_{uuid4().hex}"
        storage_key = (
            f"presentations/{presentation.session_id}/{presentation.id}/"
            f"revisions/v{next_version_number:04d}_{stored_file_id}.pptx"
        )
        storage_uri = self.storage.save_bytes(
            storage_key=storage_key,
            content=artifact_content,
            content_type=_PPTX_CONTENT_TYPE,
        )
        size_bytes = self.storage.get_size(storage_key=storage_key)
        stored_file = StoredFile(
            id=stored_file_id,
            session_id=presentation.session_id,
            task_id=request.task_id,
            kind="presentation_revision",
            file_type="pptx",
            mime_type=_PPTX_CONTENT_TYPE,
            title=f"{presentation.title} revision {next_version_number}",
            original_filename=f"{presentation.id}_v{next_version_number:04d}.pptx",
            storage_backend=self.storage.backend_name,
            storage_key=storage_key,
            storage_uri=storage_uri,
            checksum_sha256=sha256(artifact_content).hexdigest(),
            size_bytes=size_bytes if size_bytes is not None else len(artifact_content),
            owner_user_id=request.owner_user_id,
        )
        self.stored_files.create(stored_file)

        version = PresentationVersion(
            id=f"presver_{uuid4().hex}",
            presentation_id=presentation.id,
            file_id=stored_file.id,
            version_number=next_version_number,
            created_from_task_id=request.task_id,
            parent_version_id=previous_version.id if previous_version else None,
            change_summary=request.change_summary
            or f"{scope.value} revision: {', '.join(revised_slide_ids)}",
        )
        self.presentation_versions.create(version)

        updated_presentation = replace(
            presentation,
            current_file_id=stored_file.id,
            updated_at=datetime.now(timezone.utc),
        )
        self.presentations.create(updated_presentation)

        return DeckRevisionResult(
            presentation=updated_presentation,
            version=version,
            stored_file=stored_file,
            revised_plan=revised_plan,
            template_id=request.template_id,
            scope=scope,
            revised_slide_ids=revised_slide_ids,
            deltas=deltas,
            artifact_content=artifact_content,
            previous_version_id=previous_version.id if previous_version else None,
            previous_file_id=presentation.current_file_id,
        )


def _revise_slide(slide: PlannedSlide, *, instruction: str) -> PlannedSlide:
    clean_instruction = " ".join(instruction.split()).strip()
    if not clean_instruction:
        raise ValueError("Revision instruction must not be empty.")

    revised_title = _revision_title(slide.title, clean_instruction)
    revised_bullets = _revision_bullets(clean_instruction)
    speaker_notes = _append_revision_note(slide.speaker_notes, clean_instruction)
    return replace(
        slide,
        title=revised_title,
        bullets=revised_bullets,
        speaker_notes=speaker_notes,
    )


def _revision_title(previous_title: str, instruction: str) -> str:
    words = instruction.split()
    suffix = " ".join(words[:6]).strip()
    if not suffix:
        return previous_title
    return f"{previous_title[:36]} — revised: {suffix}"[:72]


def _revision_bullets(instruction: str) -> tuple[str, ...]:
    words = instruction.split()
    if not words:
        return ("Revision requested without detail",)
    chunks: list[str] = []
    for start in range(0, min(len(words), 36), 12):
        chunk = " ".join(words[start : start + 12]).strip()
        if chunk:
            chunks.append(chunk)
        if len(chunks) >= 3:
            break
    return tuple(chunks or ("Revision requested without detail",))


def _append_revision_note(existing_notes: str | None, instruction: str) -> str:
    revision_note = f"Revision instruction: {instruction}"
    if existing_notes:
        return f"{existing_notes}\n{revision_note}"
    return revision_note


def _build_delta(old_slide: PlannedSlide, new_slide: PlannedSlide) -> SlideRevisionDelta:
    return SlideRevisionDelta(
        slide_id=old_slide.slide_id,
        old_title=old_slide.title,
        new_title=new_slide.title,
        old_bullets=old_slide.bullets,
        new_bullets=new_slide.bullets,
    )
