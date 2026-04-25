from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from backend.app.domain import PresentationPlanSnapshot
from backend.app.repositories.interfaces import (
    PresentationPlanSnapshotRepository,
    PresentationRepository,
    PresentationVersionRepository,
)
from backend.app.services.slides_service.blocks import (
    BulletBlock,
    BusinessMetric,
    BusinessMetricBlock,
    ChartBlock,
    ChartType,
    ComparisonBlock,
    SlideBlock,
    SlideBlockType,
    TableBlock,
    TextBlock,
    TimelineBlock,
    TimelineItem,
)
from backend.app.services.slides_service.image_pipeline import ImageSpec, VisualIntent
from backend.app.services.slides_service.media import ImageFitMode, SlideMediaAsset
from backend.app.services.slides_service.outline import PlannedSlide, PresentationPlan, SlideType, StoryArcStage
from backend.app.services.slides_service.source_grounding import SlideCitation


_PLAN_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class PresentationPlanSnapshotService:
    snapshots: PresentationPlanSnapshotRepository
    presentations: PresentationRepository
    presentation_versions: PresentationVersionRepository | None = None

    def create_snapshot(
        self,
        *,
        presentation_id: str,
        plan: PresentationPlan,
        presentation_version_id: str | None = None,
        created_from_task_id: str | None = None,
        change_summary: str | None = None,
        snapshot_id: str | None = None,
    ) -> PresentationPlanSnapshot:
        presentation = self.presentations.get(presentation_id)
        if presentation is None:
            raise ValueError(f"Presentation '{presentation_id}' not found.")

        if presentation_version_id is not None and self.presentation_versions is not None:
            version_ids = {
                version.id
                for version in self.presentation_versions.list_by_presentation(presentation_id)
            }
            if presentation_version_id not in version_ids:
                raise ValueError(
                    f"Presentation version '{presentation_version_id}' not found for presentation '{presentation_id}'."
                )

        snapshot = PresentationPlanSnapshot(
            id=snapshot_id or f"plansnap_{uuid4().hex}",
            presentation_id=presentation_id,
            presentation_version_id=presentation_version_id,
            snapshot_json=serialize_presentation_plan(plan),
            created_from_task_id=created_from_task_id,
            change_summary=change_summary,
        )
        return self.snapshots.create(snapshot)

    def get_latest_snapshot(self, presentation_id: str) -> PresentationPlanSnapshot | None:
        return self.snapshots.get_latest_for_presentation(presentation_id)

    def get_latest_plan(self, presentation_id: str) -> PresentationPlan | None:
        snapshot = self.get_latest_snapshot(presentation_id)
        if snapshot is None:
            return None
        return deserialize_presentation_plan(snapshot.snapshot_json)

    def get_snapshot_for_version(self, presentation_version_id: str) -> PresentationPlanSnapshot | None:
        return self.snapshots.get_by_version(presentation_version_id)

    def get_plan_for_version(self, presentation_version_id: str) -> PresentationPlan | None:
        snapshot = self.get_snapshot_for_version(presentation_version_id)
        if snapshot is None:
            return None
        return deserialize_presentation_plan(snapshot.snapshot_json)


def serialize_presentation_plan(plan: PresentationPlan) -> dict[str, Any]:
    return {
        "schema_version": _PLAN_SCHEMA_VERSION,
        "deck_title": plan.deck_title,
        "deck_goal": plan.deck_goal,
        "audience": plan.audience,
        "tone": plan.tone,
        "target_slide_count": plan.target_slide_count,
        "story_arc": [stage.value for stage in plan.story_arc],
        "slides": [_serialize_slide(slide) for slide in plan.slides],
    }


def deserialize_presentation_plan(payload: dict[str, Any]) -> PresentationPlan:
    schema_version = int(payload.get("schema_version") or 1)
    if schema_version != _PLAN_SCHEMA_VERSION:
        raise ValueError(f"Unsupported presentation plan snapshot schema_version: {schema_version}")

    slides = tuple(_deserialize_slide(item) for item in _require_list(payload, "slides"))
    return PresentationPlan(
        deck_title=_require_str(payload, "deck_title"),
        deck_goal=_require_str(payload, "deck_goal"),
        audience=_require_str(payload, "audience"),
        tone=_require_str(payload, "tone"),
        target_slide_count=int(payload["target_slide_count"]),
        story_arc=tuple(StoryArcStage(stage) for stage in _require_list(payload, "story_arc")),
        slides=slides,
    )


def _serialize_slide(slide: PlannedSlide) -> dict[str, Any]:
    return {
        "slide_id": slide.slide_id,
        "slide_type": slide.slide_type.value,
        "story_arc_stage": slide.story_arc_stage.value,
        "title": slide.title,
        "bullets": list(slide.bullets),
        "speaker_notes": slide.speaker_notes,
        "layout_hint": slide.layout_hint,
        "visual_intent": slide.visual_intent.value,
        "image_specs": [_serialize_image_spec(spec) for spec in slide.image_specs],
        "media_assets": [_serialize_media_asset(asset) for asset in slide.media_assets],
        "blocks": [_serialize_block(block) for block in slide.blocks],
        "citations": [_serialize_citation(citation) for citation in slide.citations],
        "source_notes": list(slide.source_notes),
    }


def _deserialize_slide(payload: dict[str, Any]) -> PlannedSlide:
    return PlannedSlide(
        slide_id=_require_str(payload, "slide_id"),
        slide_type=SlideType(_require_str(payload, "slide_type")),
        story_arc_stage=StoryArcStage(_require_str(payload, "story_arc_stage")),
        title=_require_str(payload, "title"),
        bullets=tuple(str(item) for item in payload.get("bullets", ())),
        speaker_notes=_optional_str(payload.get("speaker_notes")),
        layout_hint=_optional_str(payload.get("layout_hint")),
        visual_intent=VisualIntent(str(payload.get("visual_intent") or VisualIntent.NONE.value)),
        image_specs=tuple(_deserialize_image_spec(item) for item in payload.get("image_specs", ())),
        media_assets=tuple(_deserialize_media_asset(item) for item in payload.get("media_assets", ())),
        blocks=tuple(_deserialize_block(item) for item in payload.get("blocks", ())),
        citations=tuple(_deserialize_citation(item) for item in payload.get("citations", ())),
        source_notes=tuple(str(item) for item in payload.get("source_notes", ())),
    )


def _serialize_image_spec(spec: ImageSpec) -> dict[str, Any]:
    return {
        "spec_id": spec.spec_id,
        "intent": spec.intent.value,
        "prompt": spec.prompt,
        "aspect_ratio": spec.aspect_ratio,
        "caption": spec.caption,
        "source_label": spec.source_label,
        "required": spec.required,
    }


def _deserialize_image_spec(payload: dict[str, Any]) -> ImageSpec:
    return ImageSpec(
        spec_id=_require_str(payload, "spec_id"),
        intent=VisualIntent(_require_str(payload, "intent")),
        prompt=_require_str(payload, "prompt"),
        aspect_ratio=str(payload.get("aspect_ratio") or "16:9"),
        caption=_optional_str(payload.get("caption")),
        source_label=_optional_str(payload.get("source_label")),
        required=bool(payload.get("required", True)),
    )


def _serialize_media_asset(asset: SlideMediaAsset) -> dict[str, Any]:
    # Binary image bytes and storage_uri intentionally stay out of metadata snapshots.
    return {
        "media_id": asset.media_id,
        "filename": asset.filename,
        "content_type": asset.content_type,
        "width_px": asset.width_px,
        "height_px": asset.height_px,
        "fit_mode": asset.fit_mode.value,
        "alt_text": asset.alt_text,
        "caption": asset.caption,
        "source_label": asset.source_label,
        "stored_file_id": asset.stored_file_id,
        "data_persisted": False,
    }


def _deserialize_media_asset(payload: dict[str, Any]) -> SlideMediaAsset:
    return SlideMediaAsset(
        media_id=_require_str(payload, "media_id"),
        filename=_require_str(payload, "filename"),
        content_type=_require_str(payload, "content_type"),
        data=b"",
        width_px=int(payload.get("width_px") or 1),
        height_px=int(payload.get("height_px") or 1),
        fit_mode=ImageFitMode(str(payload.get("fit_mode") or ImageFitMode.CONTAIN.value)),
        alt_text=_optional_str(payload.get("alt_text")),
        caption=_optional_str(payload.get("caption")),
        source_label=_optional_str(payload.get("source_label")),
        stored_file_id=_optional_str(payload.get("stored_file_id")),
        storage_uri=None,
    )


def _serialize_block(block: SlideBlock) -> dict[str, Any]:
    if isinstance(block, TextBlock):
        return {"block_type": block.block_type.value, "block_id": block.block_id, "text": block.text, "caption": block.caption}
    if isinstance(block, BulletBlock):
        return {"block_type": block.block_type.value, "block_id": block.block_id, "bullets": list(block.bullets), "heading": block.heading}
    if isinstance(block, TableBlock):
        return {
            "block_type": block.block_type.value,
            "block_id": block.block_id,
            "columns": list(block.columns),
            "rows": [list(row) for row in block.rows],
            "caption": block.caption,
        }
    if isinstance(block, ChartBlock):
        return {
            "block_type": block.block_type.value,
            "block_id": block.block_id,
            "title": block.title,
            "categories": list(block.categories),
            "values": list(block.values),
            "unit": block.unit,
            "chart_type": block.chart_type.value,
        }
    if isinstance(block, ComparisonBlock):
        return {
            "block_type": block.block_type.value,
            "block_id": block.block_id,
            "left_title": block.left_title,
            "left_items": list(block.left_items),
            "right_title": block.right_title,
            "right_items": list(block.right_items),
        }
    if isinstance(block, TimelineBlock):
        return {
            "block_type": block.block_type.value,
            "block_id": block.block_id,
            "items": [{"label": item.label, "detail": item.detail} for item in block.items],
            "caption": block.caption,
        }
    if isinstance(block, BusinessMetricBlock):
        return {
            "block_type": block.block_type.value,
            "block_id": block.block_id,
            "metrics": [{"label": item.label, "value": item.value, "note": item.note} for item in block.metrics],
            "caption": block.caption,
        }
    raise ValueError(f"Unsupported slide block type: {type(block).__name__}")


def _deserialize_block(payload: dict[str, Any]) -> SlideBlock:
    block_type = SlideBlockType(_require_str(payload, "block_type"))
    if block_type is SlideBlockType.TEXT:
        return TextBlock(block_id=_require_str(payload, "block_id"), text=_require_str(payload, "text"), caption=_optional_str(payload.get("caption")))
    if block_type is SlideBlockType.BULLET:
        return BulletBlock(
            block_id=_require_str(payload, "block_id"),
            bullets=tuple(str(item) for item in payload.get("bullets", ())),
            heading=_optional_str(payload.get("heading")),
        )
    if block_type is SlideBlockType.TABLE:
        return TableBlock(
            block_id=_require_str(payload, "block_id"),
            columns=tuple(str(item) for item in payload.get("columns", ())),
            rows=tuple(tuple(str(cell) for cell in row) for row in payload.get("rows", ())),
            caption=_optional_str(payload.get("caption")),
        )
    if block_type is SlideBlockType.CHART:
        return ChartBlock(
            block_id=_require_str(payload, "block_id"),
            title=_require_str(payload, "title"),
            categories=tuple(str(item) for item in payload.get("categories", ())),
            values=tuple(float(item) for item in payload.get("values", ())),
            unit=str(payload.get("unit") or ""),
            chart_type=ChartType(str(payload.get("chart_type") or ChartType.BAR.value)),
        )
    if block_type is SlideBlockType.COMPARISON:
        return ComparisonBlock(
            block_id=_require_str(payload, "block_id"),
            left_title=_require_str(payload, "left_title"),
            left_items=tuple(str(item) for item in payload.get("left_items", ())),
            right_title=_require_str(payload, "right_title"),
            right_items=tuple(str(item) for item in payload.get("right_items", ())),
        )
    if block_type is SlideBlockType.TIMELINE:
        return TimelineBlock(
            block_id=_require_str(payload, "block_id"),
            items=tuple(TimelineItem(label=_require_str(item, "label"), detail=_require_str(item, "detail")) for item in payload.get("items", ())),
            caption=_optional_str(payload.get("caption")),
        )
    if block_type is SlideBlockType.BUSINESS_METRIC:
        return BusinessMetricBlock(
            block_id=_require_str(payload, "block_id"),
            metrics=tuple(
                BusinessMetric(
                    label=_require_str(item, "label"),
                    value=_require_str(item, "value"),
                    note=_optional_str(item.get("note")),
                )
                for item in payload.get("metrics", ())
            ),
            caption=_optional_str(payload.get("caption")),
        )
    raise ValueError(f"Unsupported slide block type: {block_type.value}")


def _serialize_citation(citation: object) -> dict[str, Any]:
    if isinstance(citation, SlideCitation):
        return citation.as_dict()
    if hasattr(citation, "as_dict"):
        value = citation.as_dict()
        if isinstance(value, dict):
            return dict(value)
    if isinstance(citation, dict):
        return dict(citation)
    raise ValueError(f"Unsupported slide citation type: {type(citation).__name__}")


def _deserialize_citation(payload: dict[str, Any]) -> SlideCitation:
    return SlideCitation(
        citation_id=_require_str(payload, "citation_id"),
        source_kind=_require_str(payload, "source_kind"),
        source_id=_require_str(payload, "source_id"),
        fragment_id=_require_str(payload, "fragment_id"),
        source_label=_require_str(payload, "source_label"),
        excerpt=_require_str(payload, "excerpt"),
        derived_content_id=_optional_str(payload.get("derived_content_id")),
    )


def _require_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Presentation plan snapshot field '{key}' must be a non-empty string.")
    return value


def _require_list(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Presentation plan snapshot field '{key}' must be a list.")
    return value


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
