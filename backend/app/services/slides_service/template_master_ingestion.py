from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.adaptive_deck_modes import (
    DECK_MODE_IDS,
    get_adaptive_deck_mode_registry,
)
from backend.app.services.slides_service.layouts import get_template_registry
from backend.app.services.slides_service.native_visuals import get_native_visual_specs

S5_WORKFLOW_ID = "slides.template_master_ingestion"
LOCAL_TEMPLATE_SOURCE = "local_builtin_registry"
EXTERNAL_TEMPLATE_DISCOVERY_ALLOWED = False
PUBLIC_INTERNET_REQUIRED = False

FORBIDDEN_TEMPLATE_PREFIXES = (
    "http://",
    "https://",
    "s3://",
    "gs://",
    "ftp://",
    "file://",
    "//",
)

ARCHETYPE_LAYOUT_MAP: dict[str, dict[str, str]] = {
    "executive_board_deck": {
        "executive_title": "title_slide",
        "decision_request": "title_and_bullets",
        "readiness_evidence": "data_summary",
        "risk_guardrail_table": "data_summary",
        "recommendation_slide": "conclusion",
        "next_actions_owner_table": "data_summary",
    },
    "architecture_review_deck": {
        "architecture_title": "title_slide",
        "topology_map": "content_with_visual",
        "component_responsibility_matrix": "data_summary",
        "runtime_boundary_table": "two_column_comparison",
        "failure_modes_operator_gates": "data_summary",
        "release_readiness_checklist": "title_and_bullets",
        "owner_next_actions": "data_summary",
    },
    "project_status_deck": {
        "status_title": "title_slide",
        "milestone_timeline": "timeline",
        "readiness_summary": "data_summary",
        "risk_register": "data_summary",
        "open_decisions_table": "data_summary",
        "next_actions_owner_table": "data_summary",
    },
    "decision_matrix_deck": {
        "decision_title": "title_slide",
        "option_matrix": "data_summary",
        "tradeoff_summary": "two_column_comparison",
        "constraints_assumptions": "title_and_bullets",
        "recommendation_slide": "conclusion",
        "implementation_next_steps": "data_summary",
    },
    "long_document_explainer": {
        "document_title": "title_slide",
        "section_map": "content_with_visual",
        "key_concepts": "title_and_bullets",
        "structured_summary_table": "data_summary",
        "evidence_package": "data_summary",
        "risk_or_constraint_table": "data_summary",
        "claim_guard": "title_and_bullets",
        "next_steps": "conclusion",
    },
}


@dataclass(frozen=True)
class LocalTemplateMasterMetadata:
    template_id: str
    display_name: str
    theme_name: str
    font_family: str
    background_color: str
    title_color: str
    body_color: str
    accent_color: str
    layout_ids: tuple[str, ...]
    source: str = LOCAL_TEMPLATE_SOURCE
    external_discovery_allowed: bool = EXTERNAL_TEMPLATE_DISCOVERY_ALLOWED
    public_internet_required: bool = PUBLIC_INTERNET_REQUIRED

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["layout_ids"] = list(self.layout_ids)
        return payload


@dataclass(frozen=True)
class TemplateLayoutMapping:
    deck_mode_id: str
    slide_archetype: str
    layout_id: str
    template_id_required: bool
    native_visual_ready: bool
    provenance_required: bool = True
    editable_pptx_required: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_local_template_reference(template_reference: str) -> list[str]:
    errors: list[str] = []
    value = (template_reference or "").strip()
    if not value:
        return ["template reference is required"]
    normalized = value.lower()
    if any(normalized.startswith(prefix) for prefix in FORBIDDEN_TEMPLATE_PREFIXES) or "://" in normalized:
        errors.append("external template references are forbidden; use a local template id")
    if "/" in value or "\\" in value or ".." in value:
        errors.append("template references must be local template ids, not filesystem paths")
    return errors


def extract_local_template_master_metadata() -> dict[str, LocalTemplateMasterMetadata]:
    registry = get_template_registry()
    metadata: dict[str, LocalTemplateMasterMetadata] = {}
    for template_id, template in sorted(registry.items()):
        metadata[template_id] = LocalTemplateMasterMetadata(
            template_id=template.template_id,
            display_name=template.display_name,
            theme_name=template.theme_name,
            font_family=template.font_family,
            background_color=template.background_color,
            title_color=template.title_color,
            body_color=template.body_color,
            accent_color=template.accent_color,
            layout_ids=tuple(sorted(template.layouts)),
        )
    return metadata


def build_template_layout_mappings() -> tuple[TemplateLayoutMapping, ...]:
    visual_specs = get_native_visual_specs()
    native_visual_archetypes = {(spec.deck_mode_id, spec.slide_archetype) for spec in visual_specs}
    mappings: list[TemplateLayoutMapping] = []
    for deck_mode_id in DECK_MODE_IDS:
        for archetype, layout_id in sorted(ARCHETYPE_LAYOUT_MAP[deck_mode_id].items()):
            mappings.append(
                TemplateLayoutMapping(
                    deck_mode_id=deck_mode_id,
                    slide_archetype=archetype,
                    layout_id=layout_id,
                    template_id_required=True,
                    native_visual_ready=(deck_mode_id, archetype) in native_visual_archetypes,
                )
            )
    return tuple(mappings)


def validate_template_master_ingestion() -> list[str]:
    errors: list[str] = []
    templates = get_template_registry()
    metadata = extract_local_template_master_metadata()
    deck_modes = get_adaptive_deck_mode_registry()
    visual_specs = get_native_visual_specs()
    mappings = build_template_layout_mappings()

    if not templates:
        errors.append("local template registry must not be empty")
    if set(metadata) != set(templates):
        errors.append("template master metadata must cover every local template")
    for template_id, meta in metadata.items():
        errors.extend(f"{template_id}: {error}" for error in validate_local_template_reference(template_id))
        if meta.source != LOCAL_TEMPLATE_SOURCE:
            errors.append(f"{template_id}: template source must be {LOCAL_TEMPLATE_SOURCE}")
        if meta.external_discovery_allowed:
            errors.append(f"{template_id}: external template discovery must be disabled")
        if meta.public_internet_required:
            errors.append(f"{template_id}: public internet must not be required")
        for field_name in ("theme_name", "font_family", "background_color", "title_color", "body_color", "accent_color"):
            if not str(getattr(meta, field_name)).strip():
                errors.append(f"{template_id}: missing theme/master metadata field {field_name}")
        if len(meta.layout_ids) < 5:
            errors.append(f"{template_id}: expected at least five slide layouts")

    for deck_mode_id in DECK_MODE_IDS:
        if deck_mode_id not in deck_modes:
            errors.append(f"missing S3 deck mode for template mapping: {deck_mode_id}")
        if deck_mode_id not in ARCHETYPE_LAYOUT_MAP:
            errors.append(f"missing archetype layout map for {deck_mode_id}")
            continue
        mode = deck_modes.get(deck_mode_id)
        if mode:
            for archetype in mode.required_slide_archetypes:
                if archetype not in ARCHETYPE_LAYOUT_MAP[deck_mode_id]:
                    errors.append(f"{deck_mode_id}: missing template layout mapping for archetype {archetype}")

    all_layout_ids_by_template = {template_id: set(template.layouts) for template_id, template in templates.items()}
    for mapping in mappings:
        for template_id, layout_ids in all_layout_ids_by_template.items():
            if mapping.layout_id not in layout_ids:
                errors.append(f"{template_id}: missing layout {mapping.layout_id} for {mapping.deck_mode_id}/{mapping.slide_archetype}")

    visual_pairs = {(spec.deck_mode_id, spec.slide_archetype) for spec in visual_specs}
    mapped_pairs = {(mapping.deck_mode_id, mapping.slide_archetype) for mapping in mappings}
    missing_visual_mappings = sorted(visual_pairs - mapped_pairs)
    for deck_mode_id, archetype in missing_visual_mappings:
        errors.append(f"missing S4 native visual template layout mapping for {deck_mode_id}/{archetype}")

    return errors


def template_master_ingestion_report() -> dict[str, Any]:
    errors = validate_template_master_ingestion()
    metadata = extract_local_template_master_metadata()
    mappings = build_template_layout_mappings()
    visual_specs = get_native_visual_specs()
    deck_mode_ids_with_mappings = sorted({mapping.deck_mode_id for mapping in mappings})
    native_visual_pairs = {(spec.deck_mode_id, spec.slide_archetype) for spec in visual_specs}
    native_visual_mapped_count = sum(
        1 for mapping in mappings if (mapping.deck_mode_id, mapping.slide_archetype) in native_visual_pairs
    )
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S5_WORKFLOW_ID,
        "s_phase": "S5",
        "template_master_ingestion_completed_by_s5": not errors,
        "local_template_registry_count": len(metadata),
        "allowed_local_template_ids": sorted(metadata),
        "slide_master_metadata_extracted_by_s5": not errors and bool(metadata),
        "template_theme_metadata_ready_by_s5": not errors and bool(metadata),
        "s3_archetype_to_template_layout_mapping_ready_by_s5": not errors,
        "s4_native_visual_to_template_layout_mapping_ready_by_s5": not errors,
        "template_layout_mapping_count": len(mappings),
        "native_visual_template_mapping_count": native_visual_mapped_count,
        "deck_mode_count_with_template_mappings": len(deck_mode_ids_with_mappings),
        "expected_deck_mode_count": len(DECK_MODE_IDS),
        "deck_mode_ids_with_template_mappings": deck_mode_ids_with_mappings,
        "template_master_metadata": {template_id: meta.as_dict() for template_id, meta in metadata.items()},
        "template_layout_mappings": [mapping.as_dict() for mapping in mappings],
        "local_template_source_enforced_by_s5": True,
        "external_template_discovery_allowed_by_s5": False,
        "external_template_references_allowed_by_s5": False,
        "public_internet_required_by_s5": False,
        "browser_runtime_required_by_s5": False,
        "pptx_template_upload_policy_ready_by_s5": True,
        "slide_master_layout_mapping_ready_by_s5": not errors,
        "template_mode_compatible_with_s2_by_s5": True,
        "native_visuals_compatible_with_s4_by_s5": not errors,
        "api_endpoint_added_by_s5": False,
        "db_schema_migration_added_by_s5": False,
        "frontend_runtime_changed_by_s5": False,
        "dependency_versions_changed_by_s5": False,
        "dockerfiles_changed_by_s5": False,
        "cloud_llm_added_by_s5": False,
        "cloud_vision_added_by_s5": False,
        "kimi_level_claimed_by_s5": False,
        "whole_project_kimi_level_supported": False,
        "server3_local_intranet_route_verified_by_s5": False,
        "next_recommended_step": "S6 - image/screenshot-to-slide workflow through local heavy modules.",
        "errors": errors,
    }
