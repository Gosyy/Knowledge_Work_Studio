from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status

from backend.app.domain import Presentation, PresentationVersion, StoredFile
from backend.app.repositories import PresentationRepository, PresentationVersionRepository, StoredFileRepository
from backend.app.services.session_task_service import SessionTaskService


@dataclass(frozen=True)
class PresentationFileRef:
    id: str
    kind: str
    file_type: str
    mime_type: str
    title: str | None
    original_filename: str | None
    checksum_sha256: str | None
    size_bytes: int | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PresentationVersionSummary:
    id: str
    version_number: int
    file_id: str
    parent_version_id: str | None
    change_summary: str | None
    created_at: datetime


@dataclass(frozen=True)
class PresentationMetadata:
    id: str
    session_id: str
    current_file_id: str | None
    presentation_type: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    current_file: PresentationFileRef | None
    latest_version: PresentationVersionSummary | None


@dataclass
class PresentationCatalogService:
    session_task_service: SessionTaskService
    presentations: PresentationRepository
    stored_files: StoredFileRepository
    presentation_versions: PresentationVersionRepository

    def list_session_presentations_for_user(self, *, session_id: str, owner_user_id: str) -> tuple[PresentationMetadata, ...]:
        self.session_task_service.get_session_for_user(session_id, owner_user_id)
        presentations = self.presentations.list_by_session(session_id)
        return tuple(self._to_metadata(presentation) for presentation in presentations)

    def get_presentation_for_user(self, *, presentation_id: str, owner_user_id: str) -> PresentationMetadata:
        presentation = self.presentations.get(presentation_id)
        if presentation is None:
            _not_found("Presentation not found")

        self.session_task_service.get_session_for_user(presentation.session_id, owner_user_id)
        return self._to_metadata(presentation)

    def _to_metadata(self, presentation: Presentation) -> PresentationMetadata:
        current_file = self._current_file_ref(presentation.current_file_id)
        latest_version = self._latest_version_summary(presentation.id)
        return PresentationMetadata(
            id=presentation.id,
            session_id=presentation.session_id,
            current_file_id=presentation.current_file_id,
            presentation_type=presentation.presentation_type,
            title=presentation.title,
            status=presentation.status,
            created_at=presentation.created_at,
            updated_at=presentation.updated_at,
            current_file=current_file,
            latest_version=latest_version,
        )

    def _current_file_ref(self, current_file_id: str | None) -> PresentationFileRef | None:
        if current_file_id is None:
            return None
        stored_file = self.stored_files.get(current_file_id)
        if stored_file is None:
            return None
        return _file_ref(stored_file)

    def _latest_version_summary(self, presentation_id: str) -> PresentationVersionSummary | None:
        versions = self.presentation_versions.list_by_presentation(presentation_id)
        if not versions:
            return None
        latest = sorted(versions, key=lambda item: item.version_number)[-1]
        return _version_summary(latest)


def _file_ref(stored_file: StoredFile) -> PresentationFileRef:
    return PresentationFileRef(
        id=stored_file.id,
        kind=stored_file.kind,
        file_type=stored_file.file_type,
        mime_type=stored_file.mime_type,
        title=stored_file.title,
        original_filename=stored_file.original_filename,
        checksum_sha256=stored_file.checksum_sha256,
        size_bytes=stored_file.size_bytes,
        created_at=stored_file.created_at,
        updated_at=stored_file.updated_at,
    )


def _version_summary(version: PresentationVersion) -> PresentationVersionSummary:
    return PresentationVersionSummary(
        id=version.id,
        version_number=version.version_number,
        file_id=version.file_id,
        parent_version_id=version.parent_version_id,
        change_summary=version.change_summary,
        created_at=version.created_at,
    )


def _not_found(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
