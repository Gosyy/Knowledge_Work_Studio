from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

from backend.app.services.slides_service.outline import PresentationPlan

PRESENTATION_IR_SCHEMA_VERSION = "presentation_ir.v1"
PRESENTATION_IR_SOURCE_FORMAT_LEGACY_PLAN = "legacy_plan_snapshot.v1"
PRESENTATION_IR_SOURCE_FORMAT_NATIVE = "presentation_ir_native.v1"
PRESENTATION_IR_SOURCE_ATTACHMENT_CONTRACT_VERSION = "presentation_source_attachment.v1"

PresentationIRStorageFormat = Literal["presentation_ir", "legacy_plan_snapshot"]

_REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "deck",
    "theme",
    "sources",
    "assets",
    "slides",
    "quality_contract",
}


def is_presentation_ir_payload(payload: dict[str, Any]) -> bool:
    return payload.get("schema_version") == PRESENTATION_IR_SCHEMA_VERSION


def detect_presentation_ir_storage_format(payload: dict[str, Any]) -> PresentationIRStorageFormat:
    if is_presentation_ir_payload(payload):
        return "presentation_ir"
    return "legacy_plan_snapshot"


def validate_presentation_ir_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(key for key in _REQUIRED_TOP_LEVEL_KEYS if key not in payload)
    errors.extend(f"missing required PresentationIR field: {key}" for key in missing)

    if payload.get("schema_version") != PRESENTATION_IR_SCHEMA_VERSION:
        errors.append(f"schema_version must be {PRESENTATION_IR_SCHEMA_VERSION}")

    deck = payload.get("deck")
    if not isinstance(deck, dict):
        errors.append("deck must be an object")
    else:
        for key in ("title", "objective", "audience", "language", "slide_count"):
            if key not in deck:
                errors.append(f"deck.{key} is required")

    theme = payload.get("theme")
    if not isinstance(theme, dict):
        errors.append("theme must be an object")

    for key in ("sources", "assets", "slides"):
        if not isinstance(payload.get(key), list):
            errors.append(f"{key} must be a list")

    for index, source in enumerate(payload.get("sources") or []):
        if not isinstance(source, dict):
            errors.append(f"sources[{index}] must be an object")
            continue
        for key in ("source_id", "source_type", "role", "extraction_status"):
            if not str(source.get(key) or "").strip():
                errors.append(f"sources[{index}].{key} is required")
        if source.get("source_type") not in {"uploaded_file", "stored_file", "document", "presentation"}:
            errors.append(f"sources[{index}].source_type is unsupported")
        if source.get("extraction_status") not in {"not_started", "pending", "ready", "unsupported", "missing"}:
            errors.append(f"sources[{index}].extraction_status is unsupported")

    quality_contract = payload.get("quality_contract")
    if not isinstance(quality_contract, dict):
        errors.append("quality_contract must be an object")

    slide_ids: set[str] = set()
    for index, slide in enumerate(payload.get("slides") or []):
        if not isinstance(slide, dict):
            errors.append(f"slides[{index}] must be an object")
            continue
        slide_id = str(slide.get("slide_id") or "").strip()
        if not slide_id:
            errors.append(f"slides[{index}].slide_id is required")
        elif slide_id in slide_ids:
            errors.append(f"duplicate slide_id: {slide_id}")
        slide_ids.add(slide_id)
        for key in ("slide_number", "role", "title", "takeaway", "blocks", "visual_plan"):
            if key not in slide:
                errors.append(f"slides[{index}].{key} is required")
        if "blocks" in slide and not isinstance(slide.get("blocks"), list):
            errors.append(f"slides[{index}].blocks must be a list")
        if "visual_plan" in slide and not isinstance(slide.get("visual_plan"), dict):
            errors.append(f"slides[{index}].visual_plan must be an object")

    return errors


def require_presentation_ir_payload(payload: dict[str, Any]) -> dict[str, Any]:
    errors = validate_presentation_ir_payload(payload)
    if errors:
        raise ValueError("Invalid PresentationIR payload: " + "; ".join(errors))
    return deepcopy(payload)


def build_presentation_ir_from_legacy_plan(
    plan: PresentationPlan,
    *,
    presentation_id: str,
    snapshot_id: str | None = None,
    presentation_version_id: str | None = None,
    created_from_task_id: str | None = None,
) -> dict[str, Any]:
    slides: list[dict[str, Any]] = []
    for index, slide in enumerate(plan.slides, start=1):
        slides.append(
            {
                "slide_id": slide.slide_id,
                "slide_number": index,
                "role": _slide_role(slide.slide_type.value),
                "title": slide.title,
                "takeaway": slide.bullets[0] if slide.bullets else slide.title,
                "evidence": [citation.source_id for citation in slide.citations],
                "blocks": [
                    {
                        "block_id": f"{slide.slide_id}_bullets",
                        "type": "bullets",
                        "semantic_role": "supporting_evidence",
                        "content": {"items": list(slide.bullets)},
                        "data_binding": None,
                        "source_refs": [citation.source_id for citation in slide.citations],
                    }
                ],
                "visual_plan": {
                    "layout_family": slide.layout_hint or "minimal",
                    "density": "medium" if len(slide.bullets) > 2 else "low",
                    "requires_image": bool(slide.image_specs or slide.media_assets),
                    "requires_chart": any(block.__class__.__name__.lower().startswith("chart") for block in slide.blocks),
                    "requires_diagram": False,
                    "allowed_without_data": True,
                },
                "speaker_notes": slide.speaker_notes or "",
            }
        )

    payload: dict[str, Any] = {
        "schema_version": PRESENTATION_IR_SCHEMA_VERSION,
        "deck": {
            "presentation_id": presentation_id,
            "snapshot_id": snapshot_id,
            "presentation_version_id": presentation_version_id,
            "created_from_task_id": created_from_task_id,
            "title": plan.deck_title,
            "objective": plan.deck_goal,
            "audience": plan.audience,
            "tone": plan.tone,
            "scenario": "report",
            "language": "ru",
            "slide_count": len(slides),
        },
        "theme": {
            "template_id": "legacy_plan_adapter",
            "brand_source": "none",
            "font_family": "Aptos",
            "color_tokens": {},
        },
        "sources": [],
        "assets": [],
        "slides": slides,
        "quality_contract": {
            "no_fake_charts": True,
            "no_generated_images": True,
            "source_images_only": True,
            "native_editable_components": False,
            "source_format": PRESENTATION_IR_SOURCE_FORMAT_LEGACY_PLAN,
        },
    }
    return require_presentation_ir_payload(payload)


def coerce_snapshot_payload_to_presentation_ir(
    payload: dict[str, Any],
    *,
    presentation_id: str,
    snapshot_id: str | None = None,
    presentation_version_id: str | None = None,
    created_from_task_id: str | None = None,
    legacy_plan: PresentationPlan | None = None,
) -> dict[str, Any]:
    if is_presentation_ir_payload(payload):
        return require_presentation_ir_payload(payload)
    if legacy_plan is None:
        raise ValueError("legacy_plan is required to adapt a legacy plan snapshot to PresentationIR")
    return build_presentation_ir_from_legacy_plan(
        legacy_plan,
        presentation_id=presentation_id,
        snapshot_id=snapshot_id,
        presentation_version_id=presentation_version_id,
        created_from_task_id=created_from_task_id,
    )


def presentation_ir_version_metadata(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "ir_schema_version": PRESENTATION_IR_SCHEMA_VERSION,
        "storage_format": detect_presentation_ir_storage_format(payload),
    }


def presentation_ir_source_attachments(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the safe source attachment/read contract payload from PresentationIR.

    This is a read contract, not a KR-7D extraction runtime. Source objects are
    persisted inside PresentationIR and must not expose storage keys or local URIs.
    """

    presentation_ir = require_presentation_ir_payload(payload)
    sources: list[dict[str, Any]] = []
    for source in presentation_ir.get("sources", []):
        if not isinstance(source, dict):
            continue
        source_id = str(source.get("source_id") or "").strip()
        source_type = str(source.get("source_type") or "").strip()
        role = str(source.get("role") or "").strip()
        extraction_status = str(source.get("extraction_status") or "").strip()
        if not source_id or not source_type or not role or not extraction_status:
            continue
        sources.append(
            {
                "source_id": source_id,
                "source_type": source_type,
                "role": role,
                "title": source.get("title"),
                "file_type": source.get("file_type"),
                "mime_type": source.get("mime_type"),
                "checksum_sha256": source.get("checksum_sha256"),
                "size_bytes": source.get("size_bytes"),
                "extraction_status": extraction_status,
                "source_file_id": source.get("source_file_id"),
                "source_document_id": source.get("source_document_id"),
                "source_presentation_id": source.get("source_presentation_id"),
                "provenance_ref": source.get("provenance_ref"),
            }
        )
    return sources


def _slide_role(slide_type: str) -> str:
    mapping = {
        "title": "cover",
        "section": "section",
        "conclusion": "closing",
        "comparison": "comparison",
        "timeline": "roadmap",
        "data": "data",
    }
    return mapping.get(slide_type, "content")
