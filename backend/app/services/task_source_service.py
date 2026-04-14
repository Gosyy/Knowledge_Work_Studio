from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fastapi import HTTPException, status

from backend.app.domain import ArtifactSource, DerivedContent, Document, Presentation, StoredFile, UploadedFile
from backend.app.repositories import (
    ArtifactSourceRepository,
    DerivedContentRepository,
    DocumentRepository,
    FileStorage,
    PresentationRepository,
    StoredFileRepository,
    UploadedFileRepository,
)

_TEXT_FILE_TYPES = {"txt", "md", "csv", "json", "yaml", "yml", "log"}


@dataclass(frozen=True)
class ResolvedSource:
    kind: str
    source_id: str
    role: str
    content: str
    source_file_id: str | None = None
    source_document_id: str | None = None
    source_presentation_id: str | None = None

    def as_result_ref(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "source_id": self.source_id,
            "role": self.role,
        }


@dataclass(frozen=True)
class ResolvedTaskInput:
    content: str
    source_mode: str
    sources: tuple[ResolvedSource, ...]

    def as_result_refs(self) -> list[dict[str, str]]:
        return [source.as_result_ref() for source in self.sources]


@dataclass
class TaskSourceService:
    uploads: UploadedFileRepository
    stored_files: StoredFileRepository
    documents: DocumentRepository
    presentations: PresentationRepository
    artifact_sources: ArtifactSourceRepository
    derived_contents: DerivedContentRepository
    storage: FileStorage

    def build_execution_input(
        self,
        *,
        session_id: str,
        prompt_content: str | None,
        uploaded_file_ids: list[str],
        stored_file_ids: list[str],
        document_ids: list[str],
        presentation_ids: list[str],
    ) -> ResolvedTaskInput:
        has_prompt = bool(prompt_content and prompt_content.strip())
        has_uploaded_sources = bool(uploaded_file_ids)
        has_stored_sources = bool(stored_file_ids or document_ids or presentation_ids)

        selected_modes = sum(
            1 for enabled in (has_prompt, has_uploaded_sources, has_stored_sources) if enabled
        )
        if selected_modes != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "G2 execution requests must use exactly one input mode: "
                    "prompt-only, uploaded-source, or stored-source."
                ),
            )

        if has_prompt:
            return ResolvedTaskInput(
                content=prompt_content.strip(),
                source_mode="prompt_only",
                sources=(),
            )

        if has_uploaded_sources:
            sources = tuple(
                self._resolve_uploaded_source(session_id=session_id, upload_id=upload_id)
                for upload_id in uploaded_file_ids
            )
            return ResolvedTaskInput(
                content="\n\n".join(source.content for source in sources),
                source_mode="uploaded_source",
                sources=sources,
            )

        sources = [
            self._resolve_stored_file_source(session_id=session_id, stored_file_id=stored_file_id)
            for stored_file_id in stored_file_ids
        ]
        sources.extend(
            self._resolve_document_source(session_id=session_id, document_id=document_id)
            for document_id in document_ids
        )
        sources.extend(
            self._resolve_presentation_source(session_id=session_id, presentation_id=presentation_id)
            for presentation_id in presentation_ids
        )
        return ResolvedTaskInput(
            content="\n\n".join(source.content for source in sources),
            source_mode="stored_source",
            sources=tuple(sources),
        )

    def record_artifact_sources(
        self,
        *,
        artifact_ids: list[str],
        sources: tuple[ResolvedSource, ...],
    ) -> None:
        for artifact_id in artifact_ids:
            for source in sources:
                self.artifact_sources.create(
                    ArtifactSource(
                        id=f"asrc_{uuid4().hex}",
                        artifact_id=artifact_id,
                        source_file_id=source.source_file_id,
                        source_document_id=source.source_document_id,
                        source_presentation_id=source.source_presentation_id,
                        role=source.role,
                    )
                )

    def _resolve_uploaded_source(self, *, session_id: str, upload_id: str) -> ResolvedSource:
        uploaded = self.uploads.get(upload_id)
        if uploaded is None or uploaded.session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Uploaded source '{upload_id}' not found for this session.",
            )

        mirrored_stored_file = self.stored_files.get(upload_id)
        if mirrored_stored_file is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Uploaded source '{upload_id}' is not registered in stored_files yet."
                ),
            )

        content = self._content_from_stored_file(
            stored_file=mirrored_stored_file,
            source_label=f"uploaded source '{upload_id}'",
        )
        return ResolvedSource(
            kind="uploaded_file",
            source_id=upload_id,
            role="primary_source",
            content=content,
            source_file_id=upload_id,
        )

    def _resolve_stored_file_source(self, *, session_id: str, stored_file_id: str) -> ResolvedSource:
        stored_file = self.stored_files.get(stored_file_id)
        if stored_file is None or stored_file.session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stored file source '{stored_file_id}' not found for this session.",
            )

        content = self._content_from_stored_file(
            stored_file=stored_file,
            source_label=f"stored file '{stored_file_id}'",
        )
        return ResolvedSource(
            kind="stored_file",
            source_id=stored_file_id,
            role="primary_source",
            content=content,
            source_file_id=stored_file_id,
        )

    def _resolve_document_source(self, *, session_id: str, document_id: str) -> ResolvedSource:
        document = self.documents.get(document_id)
        if document is None or document.session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document source '{document_id}' not found for this session.",
            )
        stored_file = self._require_current_file_for_document(document)
        content = self._content_from_stored_file(
            stored_file=stored_file,
            source_label=f"document '{document_id}'",
        )
        return ResolvedSource(
            kind="document",
            source_id=document_id,
            role="primary_source",
            content=content,
            source_document_id=document_id,
        )

    def _resolve_presentation_source(
        self,
        *,
        session_id: str,
        presentation_id: str,
    ) -> ResolvedSource:
        presentation = self.presentations.get(presentation_id)
        if presentation is None or presentation.session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Presentation source '{presentation_id}' not found for this session.",
            )
        stored_file = self._require_current_file_for_presentation(presentation)
        content = self._content_from_stored_file(
            stored_file=stored_file,
            source_label=f"presentation '{presentation_id}'",
        )
        return ResolvedSource(
            kind="presentation",
            source_id=presentation_id,
            role="primary_source",
            content=content,
            source_presentation_id=presentation_id,
        )

    def _require_current_file_for_document(self, document: Document) -> StoredFile:
        if document.current_file_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document '{document.id}' has no current_file_id for source execution.",
            )
        stored_file = self.stored_files.get(document.current_file_id)
        if stored_file is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document '{document.id}' points to a missing stored file.",
            )
        return stored_file

    def _require_current_file_for_presentation(self, presentation: Presentation) -> StoredFile:
        if presentation.current_file_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Presentation '{presentation.id}' has no current_file_id for source execution.",
            )
        stored_file = self.stored_files.get(presentation.current_file_id)
        if stored_file is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Presentation '{presentation.id}' points to a missing stored file.",
            )
        return stored_file

    def _content_from_stored_file(
        self,
        *,
        stored_file: StoredFile,
        source_label: str,
    ) -> str:
        cached_text = self._get_cached_extracted_text(stored_file.id)
        if cached_text is not None:
            return cached_text

        content = self._read_text_content(
            storage_key=stored_file.storage_key,
            file_type=stored_file.file_type,
            mime_type=stored_file.mime_type,
            source_label=source_label,
        )
        self.derived_contents.create(
            DerivedContent(
                id=f"dcon_{uuid4().hex}",
                file_id=stored_file.id,
                content_kind="extracted_text",
                text_content=content,
                structured_json=None,
                outline_json=None,
                language=None,
            )
        )
        return content

    def _get_cached_extracted_text(self, file_id: str) -> str | None:
        for derived_content in self.derived_contents.list_by_file(file_id):
            if (
                derived_content.content_kind == "extracted_text"
                and derived_content.text_content is not None
            ):
                return derived_content.text_content
        return None

    def _read_text_content(
        self,
        *,
        storage_key: str,
        file_type: str,
        mime_type: str,
        source_label: str,
    ) -> str:
        normalized_file_type = (file_type or "").lower()
        normalized_mime_type = (mime_type or "").lower()
        is_text_like = normalized_mime_type.startswith("text/") or normalized_file_type in _TEXT_FILE_TYPES
        if not is_text_like:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"{source_label} is not text-compatible for official G2 execution yet. "
                    "Binary/non-text source extraction belongs to later phases."
                ),
            )
        raw_content = self.storage.read_bytes(storage_key=storage_key)
        return raw_content.decode("utf-8", errors="replace")
