from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SLIDES_PROVENANCE_WORKFLOW_ID = "slides.provenance_manifest"
SLIDES_PROVENANCE_MANIFEST_SCHEMA_VERSION = 1

PROVENANCE_SOURCE_KINDS = (
    "uploaded_file",
    "source_document",
    "source_presentation",
    "saved_plan_snapshot",
    "operator_instruction",
    "render_mode_selection",
    "task_event_stream",
)

PROVENANCE_ARTIFACT_KINDS = (
    "pptx",
    "plan_snapshot",
    "diff",
    "provenance_manifest",
)

PROVENANCE_REQUIRED_MANIFEST_FIELDS = (
    "manifest_id",
    "schema_version",
    "workflow_id",
    "session_id",
    "task_id",
    "presentation_id",
    "created_at",
    "sources",
    "plan_snapshot",
    "render_attempt",
    "artifact",
    "event_refs",
    "integrity",
)

PROVENANCE_REQUIRED_SOURCE_FIELDS = (
    "source_id",
    "source_kind",
    "role",
    "created_at",
)

PROVENANCE_REQUIRED_PLAN_FIELDS = (
    "plan_snapshot_id",
    "presentation_id",
    "schema_version",
    "deck_title",
    "slide_count",
)

PROVENANCE_REQUIRED_RENDER_FIELDS = (
    "render_mode",
    "layout_policy",
    "template_source",
    "render_event_id",
)

PROVENANCE_REQUIRED_ARTIFACT_FIELDS = (
    "artifact_id",
    "filename",
    "content_type",
    "storage_backend",
    "size_bytes",
)

PROVENANCE_REQUIRED_INTEGRITY_FIELDS = (
    "manifest_digest",
    "artifact_checksum_sha256",
    "redaction_policy",
)

PROVENANCE_REQUIRED_EVENT_TYPES = (
    "slides.plan.approved",
    "slides.render_mode.selected",
    "slides.generation.started",
    "artifact.registered",
    "plan.snapshot.registered",
    "slides.generation.completed",
)

PROVENANCE_RETRY_REQUIRED_EVENT_TYPES = (
    "slides.retry.from_saved_plan.requested",
    "slides.retry.saved_plan_snapshot.loaded",
    "slides.retry.plan.validated",
    "slides.retry.render_mode.confirmed",
    "slides.retry.generation.started",
    "artifact.registered",
    "plan.snapshot.registered",
    "slides.retry.generation.completed",
)

PROVENANCE_REDACTED_FIELDS = (
    "password",
    "secret",
    "token",
    "api_key",
    "client_secret",
    "database_url",
    "authorization",
    "raw_prompt",
    "raw_llm_response",
)

PROVENANCE_RETRY_REQUIRED_LINK_FIELDS = (
    "parent_task_id",
    "parent_plan_snapshot_id",
    "parent_presentation_version_id",
    "retry_instruction_digest",
    "new_plan_snapshot_id",
    "new_artifact_id",
)


@dataclass(frozen=True)
class SlidesProvenanceManifestContract:
    workflow_id: str
    title: str
    schema_version: int
    offline_ready: bool
    browser_policy: str
    source_kinds: tuple[str, ...]
    artifact_kinds: tuple[str, ...]
    required_manifest_fields: tuple[str, ...]
    required_source_fields: tuple[str, ...]
    required_plan_fields: tuple[str, ...]
    required_render_fields: tuple[str, ...]
    required_artifact_fields: tuple[str, ...]
    required_integrity_fields: tuple[str, ...]
    generation_required_event_types: tuple[str, ...]
    retry_required_event_types: tuple[str, ...]
    retry_required_link_fields: tuple[str, ...]
    redacted_fields: tuple[str, ...]
    append_only_event_refs: bool
    source_to_artifact_links_required: bool
    plan_snapshot_link_required: bool
    render_mode_metadata_required: bool
    retry_parent_links_required: bool
    manifest_must_be_downloadable_artifact: bool
    non_goals: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


SLIDES_PROVENANCE_MANIFEST_CONTRACT = SlidesProvenanceManifestContract(
    workflow_id=SLIDES_PROVENANCE_WORKFLOW_ID,
    title="Slides source-to-artifact provenance manifest contract",
    schema_version=SLIDES_PROVENANCE_MANIFEST_SCHEMA_VERSION,
    offline_ready=True,
    browser_policy="none",
    source_kinds=PROVENANCE_SOURCE_KINDS,
    artifact_kinds=PROVENANCE_ARTIFACT_KINDS,
    required_manifest_fields=PROVENANCE_REQUIRED_MANIFEST_FIELDS,
    required_source_fields=PROVENANCE_REQUIRED_SOURCE_FIELDS,
    required_plan_fields=PROVENANCE_REQUIRED_PLAN_FIELDS,
    required_render_fields=PROVENANCE_REQUIRED_RENDER_FIELDS,
    required_artifact_fields=PROVENANCE_REQUIRED_ARTIFACT_FIELDS,
    required_integrity_fields=PROVENANCE_REQUIRED_INTEGRITY_FIELDS,
    generation_required_event_types=PROVENANCE_REQUIRED_EVENT_TYPES,
    retry_required_event_types=PROVENANCE_RETRY_REQUIRED_EVENT_TYPES,
    retry_required_link_fields=PROVENANCE_RETRY_REQUIRED_LINK_FIELDS,
    redacted_fields=PROVENANCE_REDACTED_FIELDS,
    append_only_event_refs=True,
    source_to_artifact_links_required=True,
    plan_snapshot_link_required=True,
    render_mode_metadata_required=True,
    retry_parent_links_required=True,
    manifest_must_be_downloadable_artifact=True,
    non_goals=(
        "No PPTX renderer rewrite in S7.",
        "No new async runtime or event store migration in S7.",
        "No full slide editor expansion in S7.",
        "No browser or internet dependency in S7.",
    ),
)


def _missing(mapping: dict[str, Any], fields: tuple[str, ...], label: str) -> list[str]:
    return [f"{label}: missing {field}" for field in fields if field not in mapping]


def _missing_items(items: tuple[str, ...], required: tuple[str, ...], label: str) -> list[str]:
    return [f"{label}: missing {item}" for item in required if item not in items]


def validate_slides_provenance_manifest_contract(
    contract: SlidesProvenanceManifestContract = SLIDES_PROVENANCE_MANIFEST_CONTRACT,
) -> list[str]:
    errors: list[str] = []
    if contract.workflow_id != SLIDES_PROVENANCE_WORKFLOW_ID:
        errors.append("workflow_id must be slides.provenance_manifest")
    if contract.schema_version != SLIDES_PROVENANCE_MANIFEST_SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if not contract.offline_ready:
        errors.append("offline_ready must be true")
    if contract.browser_policy != "none":
        errors.append("slides provenance manifest must not require browser runtime")
    if not contract.append_only_event_refs:
        errors.append("event refs must be append-only")
    if not contract.source_to_artifact_links_required:
        errors.append("source-to-artifact links are required")
    if not contract.plan_snapshot_link_required:
        errors.append("plan_snapshot link is required")
    if not contract.render_mode_metadata_required:
        errors.append("render_mode metadata is required")
    if not contract.retry_parent_links_required:
        errors.append("retry parent links are required")
    if not contract.manifest_must_be_downloadable_artifact:
        errors.append("manifest must be registered as downloadable artifact")

    errors.extend(_missing_items(contract.source_kinds, PROVENANCE_SOURCE_KINDS, "source kinds"))
    errors.extend(_missing_items(contract.artifact_kinds, PROVENANCE_ARTIFACT_KINDS, "artifact kinds"))
    errors.extend(
        _missing_items(
            contract.required_manifest_fields,
            PROVENANCE_REQUIRED_MANIFEST_FIELDS,
            "manifest fields",
        )
    )
    errors.extend(
        _missing_items(
            contract.generation_required_event_types,
            PROVENANCE_REQUIRED_EVENT_TYPES,
            "generation events",
        )
    )
    errors.extend(
        _missing_items(
            contract.retry_required_event_types,
            PROVENANCE_RETRY_REQUIRED_EVENT_TYPES,
            "retry events",
        )
    )
    errors.extend(
        _missing_items(
            contract.retry_required_link_fields,
            PROVENANCE_RETRY_REQUIRED_LINK_FIELDS,
            "retry links",
        )
    )
    for field in ("secret", "token", "api_key", "client_secret", "database_url", "raw_prompt"):
        if field not in contract.redacted_fields:
            errors.append(f"missing redacted field policy: {field}")
    return errors


def validate_manifest_payload(
    manifest: dict[str, Any],
    *,
    retry: bool = False,
    contract: SlidesProvenanceManifestContract = SLIDES_PROVENANCE_MANIFEST_CONTRACT,
) -> list[str]:
    errors = validate_slides_provenance_manifest_contract(contract)
    errors.extend(_missing(manifest, contract.required_manifest_fields, "manifest"))

    if manifest.get("workflow_id") != contract.workflow_id:
        errors.append("manifest.workflow_id must match contract workflow_id")
    if manifest.get("schema_version") != contract.schema_version:
        errors.append("manifest.schema_version must match contract schema_version")

    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("manifest.sources must be a non-empty list")
    else:
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                errors.append(f"sources[{index}] must be an object")
                continue
            errors.extend(_missing(source, contract.required_source_fields, f"sources[{index}]"))
            source_kind = source.get("source_kind")
            if source_kind not in contract.source_kinds:
                errors.append(f"sources[{index}]: unknown source_kind {source_kind!r}")

    plan_snapshot = manifest.get("plan_snapshot")
    if not isinstance(plan_snapshot, dict):
        errors.append("manifest.plan_snapshot must be an object")
    else:
        errors.extend(_missing(plan_snapshot, contract.required_plan_fields, "plan_snapshot"))

    render_attempt = manifest.get("render_attempt")
    if not isinstance(render_attempt, dict):
        errors.append("manifest.render_attempt must be an object")
    else:
        errors.extend(_missing(render_attempt, contract.required_render_fields, "render_attempt"))
        render_mode = render_attempt.get("render_mode")
        if render_mode not in {"adaptive", "template"}:
            errors.append("render_attempt.render_mode must be adaptive or template")
        if render_mode == "template" and not render_attempt.get("template_id"):
            errors.append("template render provenance must include template_id")

    artifact = manifest.get("artifact")
    if not isinstance(artifact, dict):
        errors.append("manifest.artifact must be an object")
    else:
        errors.extend(_missing(artifact, contract.required_artifact_fields, "artifact"))
        if artifact.get("content_type") != "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            errors.append("artifact.content_type must describe a PPTX artifact")

    integrity = manifest.get("integrity")
    if not isinstance(integrity, dict):
        errors.append("manifest.integrity must be an object")
    else:
        errors.extend(_missing(integrity, contract.required_integrity_fields, "integrity"))
        if integrity.get("redaction_policy") != "safe_payload_only":
            errors.append("integrity.redaction_policy must be safe_payload_only")

    event_refs = manifest.get("event_refs")
    required_events = contract.retry_required_event_types if retry else contract.generation_required_event_types
    if not isinstance(event_refs, list):
        errors.append("manifest.event_refs must be a list")
    else:
        event_types = [event.get("event_type") for event in event_refs if isinstance(event, dict)]
        for event_type in required_events:
            if event_type not in event_types:
                errors.append(f"missing event_ref: {event_type}")

    retry_links = manifest.get("retry_links")
    if retry:
        if not isinstance(retry_links, dict):
            errors.append("retry manifest must include retry_links object")
        else:
            errors.extend(_missing(retry_links, contract.retry_required_link_fields, "retry_links"))
    elif retry_links:
        errors.append("generation manifest must not include retry_links")

    forbidden_key_hits: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = key.lower()
                if normalized in contract.redacted_fields:
                    forbidden_key_hits.append(f"{path}.{key}")
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(manifest, "manifest")
    if forbidden_key_hits:
        errors.append("manifest contains forbidden raw secret/prompt fields: " + ", ".join(forbidden_key_hits))

    return errors


def sample_generation_manifest() -> dict[str, Any]:
    return {
        "manifest_id": "prov_slides_generation_contract",
        "schema_version": SLIDES_PROVENANCE_MANIFEST_SCHEMA_VERSION,
        "workflow_id": SLIDES_PROVENANCE_WORKFLOW_ID,
        "session_id": "ses_contract",
        "task_id": "task_contract_generate",
        "presentation_id": "pres_contract",
        "created_at": "2026-05-01T00:00:00Z",
        "sources": [
            {
                "source_id": "upload_contract_source",
                "source_kind": "uploaded_file",
                "role": "primary_source",
                "created_at": "2026-05-01T00:00:00Z",
                "checksum_sha256": "sha256-source",
            },
            {
                "source_id": "plansnap_contract_v1",
                "source_kind": "saved_plan_snapshot",
                "role": "approved_plan",
                "created_at": "2026-05-01T00:00:00Z",
            },
        ],
        "plan_snapshot": {
            "plan_snapshot_id": "plansnap_contract_v1",
            "presentation_id": "pres_contract",
            "schema_version": 1,
            "deck_title": "Contract deck",
            "slide_count": 3,
        },
        "render_attempt": {
            "render_mode": "adaptive",
            "layout_policy": "select_layouts_from_approved_plan_and_local_template_library",
            "template_source": "bundled_local",
            "render_event_id": "evt_render_selected",
        },
        "artifact": {
            "artifact_id": "artifact_contract_pptx",
            "filename": "contract-deck.pptx",
            "content_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "storage_backend": "local",
            "size_bytes": 4096,
        },
        "event_refs": [
            {"event_id": "evt_plan_approved", "event_type": "slides.plan.approved"},
            {"event_id": "evt_render_selected", "event_type": "slides.render_mode.selected"},
            {"event_id": "evt_generation_started", "event_type": "slides.generation.started"},
            {"event_id": "evt_artifact_registered", "event_type": "artifact.registered"},
            {"event_id": "evt_plan_snapshot_registered", "event_type": "plan.snapshot.registered"},
            {"event_id": "evt_generation_completed", "event_type": "slides.generation.completed"},
        ],
        "integrity": {
            "manifest_digest": "sha256-manifest",
            "artifact_checksum_sha256": "sha256-artifact",
            "redaction_policy": "safe_payload_only",
        },
    }


def sample_retry_manifest() -> dict[str, Any]:
    manifest = sample_generation_manifest()
    manifest = {
        **manifest,
        "manifest_id": "prov_slides_retry_contract",
        "task_id": "task_contract_retry",
        "render_attempt": {
            "render_mode": "template",
            "layout_policy": "render_with_operator_selected_local_template_id",
            "template_source": "bundled_local",
            "template_id": "board_review_local",
            "render_event_id": "evt_retry_render_confirmed",
        },
        "artifact": {
            "artifact_id": "artifact_contract_retry_pptx",
            "filename": "contract-deck-retry.pptx",
            "content_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "storage_backend": "local",
            "size_bytes": 8192,
        },
        "event_refs": [
            {"event_id": "evt_retry_requested", "event_type": "slides.retry.from_saved_plan.requested"},
            {"event_id": "evt_retry_snapshot_loaded", "event_type": "slides.retry.saved_plan_snapshot.loaded"},
            {"event_id": "evt_retry_plan_validated", "event_type": "slides.retry.plan.validated"},
            {"event_id": "evt_retry_render_confirmed", "event_type": "slides.retry.render_mode.confirmed"},
            {"event_id": "evt_retry_generation_started", "event_type": "slides.retry.generation.started"},
            {"event_id": "evt_retry_artifact_registered", "event_type": "artifact.registered"},
            {"event_id": "evt_retry_plan_snapshot_registered", "event_type": "plan.snapshot.registered"},
            {"event_id": "evt_retry_generation_completed", "event_type": "slides.retry.generation.completed"},
        ],
        "retry_links": {
            "parent_task_id": "task_contract_generate",
            "parent_plan_snapshot_id": "plansnap_contract_v1",
            "parent_presentation_version_id": "presver_contract_v1",
            "retry_instruction_digest": "sha256-instruction",
            "new_plan_snapshot_id": "plansnap_contract_v2",
            "new_artifact_id": "artifact_contract_retry_pptx",
        },
    }
    manifest["sources"] = [
        *manifest["sources"],
        {
            "source_id": "evt_retry_requested",
            "source_kind": "operator_instruction",
            "role": "retry_instruction_digest",
            "created_at": "2026-05-01T00:00:00Z",
        },
    ]
    return manifest


def slides_provenance_manifest_report(
    *,
    mode: str = "generation",
    contract: SlidesProvenanceManifestContract = SLIDES_PROVENANCE_MANIFEST_CONTRACT,
) -> dict[str, Any]:
    contract_errors = validate_slides_provenance_manifest_contract(contract)
    if mode == "generation":
        manifest = sample_generation_manifest()
        payload_errors = validate_manifest_payload(manifest, retry=False, contract=contract)
    elif mode == "retry":
        manifest = sample_retry_manifest()
        payload_errors = validate_manifest_payload(manifest, retry=True, contract=contract)
    elif mode == "contract":
        manifest = {}
        payload_errors = []
    else:
        manifest = {}
        payload_errors = [f"unknown provenance mode: {mode}"]

    errors = contract_errors + payload_errors
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": contract.workflow_id,
        "schema_version": contract.schema_version,
        "selected_mode": mode,
        "contract": contract.as_dict(),
        "sample_manifest": manifest,
        "errors": errors,
    }
