from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class StoredFile:
    id: str
    session_id: str
    task_id: str | None
    kind: str
    file_type: str
    mime_type: str
    title: str | None
    original_filename: str | None
    storage_backend: str
    storage_key: str
    storage_uri: str
    checksum_sha256: str | None
    size_bytes: int | None
    is_remote: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class Document:
    id: str
    session_id: str
    current_file_id: str | None
    document_type: str
    title: str
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class DocumentVersion:
    id: str
    document_id: str
    file_id: str
    version_number: int
    created_from_task_id: str | None
    parent_version_id: str | None
    change_summary: str | None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class Presentation:
    id: str
    session_id: str
    current_file_id: str | None
    presentation_type: str
    title: str
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PresentationVersion:
    id: str
    presentation_id: str
    file_id: str
    version_number: int
    created_from_task_id: str | None
    parent_version_id: str | None
    change_summary: str | None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class ArtifactSource:
    id: str
    artifact_id: str
    source_file_id: str | None
    source_document_id: str | None
    source_presentation_id: str | None
    role: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class DerivedContent:
    id: str
    file_id: str
    content_kind: str
    text_content: str | None
    structured_json: dict[str, Any] | None
    outline_json: dict[str, Any] | None
    language: str | None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
