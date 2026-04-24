from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


_UNSAFE_PUBLIC_KEYS = {
    "storage_key",
    "storage_uri",
    "local_path",
    "filesystem_path",
    "absolute_path",
}


class SlideOutlineItemSchema(BaseModel):
    title: str
    bullets: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class SlidesGeneratedMediaRefSchema(BaseModel):
    stored_file_id: str
    role: str = "generated_slide_media"

    model_config = ConfigDict(extra="forbid")


class SlidesSourceRefSchema(BaseModel):
    kind: str
    source_id: str
    role: str
    source_file_id: str | None = None
    source_document_id: str | None = None
    source_presentation_id: str | None = None
    derived_content_id: str | None = None

    model_config = ConfigDict(extra="forbid")


class SlideCitationSchema(BaseModel):
    citation_id: str
    source_kind: str
    source_id: str
    fragment_id: str
    source_label: str
    excerpt: str
    derived_content_id: str | None = None

    model_config = ConfigDict(extra="forbid")


class SourceGroundingMetadataSchema(BaseModel):
    citation_count: int = 0
    citations: list[SlideCitationSchema] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class SlidesTaskResultDataSchema(BaseModel):
    """Stable public shape for task.result_data when task_type == slides_generate."""

    task_type: Literal["slides_generate"]
    output_text: str | None = None
    artifact_ids: list[str] = Field(default_factory=list)
    outline: list[SlideOutlineItemSchema] = Field(default_factory=list)
    slide_count: int | None = None
    generated_media_file_ids: list[str] = Field(default_factory=list)
    generated_media_refs: list[SlidesGeneratedMediaRefSchema] = Field(default_factory=list)
    source_grounding_metadata: SourceGroundingMetadataSchema | None = None
    source_mode: str | None = None
    source_refs: list[SlidesSourceRefSchema] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def _populate_media_refs(self) -> "SlidesTaskResultDataSchema":
        if not self.generated_media_refs and self.generated_media_file_ids:
            self.generated_media_refs = [
                SlidesGeneratedMediaRefSchema(stored_file_id=file_id)
                for file_id in self.generated_media_file_ids
            ]
        return self


def normalize_public_task_result_data(result_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize public task result metadata without leaking unsafe storage internals."""
    if result_data.get("task_type") != "slides_generate":
        return dict(result_data)

    _raise_if_unsafe_keys(result_data)
    normalized = SlidesTaskResultDataSchema.model_validate(result_data)
    payload = normalized.model_dump(mode="python", exclude_none=True)
    _raise_if_unsafe_keys(payload)
    return payload


def _raise_if_unsafe_keys(value: object, *, path: str = "result_data") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in _UNSAFE_PUBLIC_KEYS:
                raise ValueError(f"Unsafe slides API metadata key '{key}' at {path}.")
            _raise_if_unsafe_keys(item, path=f"{path}.{key}")
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            _raise_if_unsafe_keys(item, path=f"{path}[{index}]")
