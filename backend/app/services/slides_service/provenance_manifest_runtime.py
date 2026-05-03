from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Protocol

from backend.app.domain import Artifact, PresentationPlanSnapshot
from backend.app.services.slides_service.approved_plan import ApprovedPlanRenderResult
from backend.app.services.slides_service.approved_plan_lifecycle import ApprovedPlanLifecycleResult, SlidesTaskEvent
from backend.app.services.slides_service.provenance_manifest_contract import (
    SLIDES_PROVENANCE_MANIFEST_SCHEMA_VERSION,
    SLIDES_PROVENANCE_WORKFLOW_ID,
    validate_manifest_payload,
)
from backend.app.services.slides_service.saved_plan_retry import SavedPlanRetryResult

PROVENANCE_MANIFEST_CONTENT_TYPE = "application/vnd.kwstudio.slides-provenance+json"
PROVENANCE_MANIFEST_REDACTION_POLICY = "safe_payload_only"


class ProvenanceArtifactRegistrationService(Protocol):
    def create_artifact_from_bytes(
        self,
        *,
        session_id: str,
        task_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Artifact: ...


@dataclass(frozen=True)
class SlidesProvenanceManifestEmissionResult:
    manifest: dict[str, Any]
    manifest_content: bytes
    manifest_artifact: Artifact
    safe_metadata: dict[str, object]


@dataclass(frozen=True)
class SlidesGenerationProvenanceRuntimeResult:
    lifecycle_result: ApprovedPlanLifecycleResult
    provenance_result: SlidesProvenanceManifestEmissionResult

    @property
    def safe_metadata(self) -> dict[str, object]:
        return {
            **self.lifecycle_result.safe_metadata,
            **self.provenance_result.safe_metadata,
        }


@dataclass(frozen=True)
class SlidesRetryProvenanceRuntimeResult:
    retry_result: SavedPlanRetryResult
    provenance_result: SlidesProvenanceManifestEmissionResult

    @property
    def safe_metadata(self) -> dict[str, object]:
        return {
            **self.retry_result.safe_metadata,
            **self.provenance_result.safe_metadata,
        }


def emit_generation_provenance_manifest(
    lifecycle_result: ApprovedPlanLifecycleResult,
    *,
    artifact_service: ProvenanceArtifactRegistrationService,
    manifest_filename: str | None = None,
) -> SlidesProvenanceManifestEmissionResult:
    """Emit a downloadable provenance manifest artifact for an approved-plan render.

    RF2.6 is additive: it links the already-registered PPTX artifact, plan
    snapshot, render-mode metadata, and append-only event refs into a separate
    JSON artifact without adding endpoints, schema migrations, queues, visual QA,
    or Kimi-level claims.
    """

    session_id = _require_metadata_str(lifecycle_result.safe_metadata, "session_id")
    task_id = _require_metadata_str(lifecycle_result.safe_metadata, "task_id")
    manifest = build_generation_provenance_manifest(lifecycle_result)
    _assert_manifest_valid(manifest, retry=False)
    content = _manifest_bytes(manifest)
    artifact = artifact_service.create_artifact_from_bytes(
        session_id=session_id,
        task_id=task_id,
        filename=manifest_filename or _default_manifest_filename(lifecycle_result.artifact.filename),
        content_type=PROVENANCE_MANIFEST_CONTENT_TYPE,
        content=content,
    )
    return _emission_result(
        manifest=manifest,
        content=content,
        artifact=artifact,
        pptx_artifact=lifecycle_result.artifact,
        retry=False,
    )


def emit_retry_provenance_manifest(
    retry_result: SavedPlanRetryResult,
    *,
    artifact_service: ProvenanceArtifactRegistrationService,
    manifest_filename: str | None = None,
) -> SlidesProvenanceManifestEmissionResult:
    """Emit a downloadable provenance manifest artifact for a saved-plan retry."""

    session_id = _require_metadata_str(retry_result.safe_metadata, "session_id")
    task_id = _require_metadata_str(retry_result.safe_metadata, "retry_task_id")
    manifest = build_retry_provenance_manifest(retry_result)
    _assert_manifest_valid(manifest, retry=True)
    content = _manifest_bytes(manifest)
    artifact = artifact_service.create_artifact_from_bytes(
        session_id=session_id,
        task_id=task_id,
        filename=manifest_filename or _default_manifest_filename(retry_result.artifact.filename),
        content_type=PROVENANCE_MANIFEST_CONTENT_TYPE,
        content=content,
    )
    return _emission_result(
        manifest=manifest,
        content=content,
        artifact=artifact,
        pptx_artifact=retry_result.artifact,
        retry=True,
    )


def build_generation_provenance_manifest(
    lifecycle_result: ApprovedPlanLifecycleResult,
) -> dict[str, Any]:
    render_result = lifecycle_result.render_result
    plan_snapshot = lifecycle_result.plan_snapshot
    artifact = lifecycle_result.artifact
    metadata = lifecycle_result.safe_metadata
    manifest = {
        "manifest_id": f"prov_{artifact.id}",
        "schema_version": SLIDES_PROVENANCE_MANIFEST_SCHEMA_VERSION,
        "workflow_id": SLIDES_PROVENANCE_WORKFLOW_ID,
        "session_id": _require_metadata_str(metadata, "session_id"),
        "task_id": _require_metadata_str(metadata, "task_id"),
        "presentation_id": plan_snapshot.presentation_id,
        "created_at": _utc_now(),
        "sources": _generation_sources(plan_snapshot, lifecycle_result.events),
        "plan_snapshot": _plan_snapshot_payload(plan_snapshot),
        "render_attempt": _render_attempt_payload(render_result, lifecycle_result.events, retry=False),
        "artifact": _artifact_payload(artifact),
        "event_refs": _event_refs(lifecycle_result.events),
        "integrity": {
            "manifest_digest": "",
            "artifact_checksum_sha256": _checksum(render_result),
            "redaction_policy": PROVENANCE_MANIFEST_REDACTION_POLICY,
        },
    }
    return _with_manifest_digest(manifest)


def build_retry_provenance_manifest(retry_result: SavedPlanRetryResult) -> dict[str, Any]:
    render_result = retry_result.render_result
    new_snapshot = retry_result.new_plan_snapshot
    parent_snapshot = retry_result.saved_plan_snapshot
    artifact = retry_result.artifact
    metadata = retry_result.safe_metadata
    manifest = {
        "manifest_id": f"prov_{artifact.id}",
        "schema_version": SLIDES_PROVENANCE_MANIFEST_SCHEMA_VERSION,
        "workflow_id": SLIDES_PROVENANCE_WORKFLOW_ID,
        "session_id": _require_metadata_str(metadata, "session_id"),
        "task_id": _require_metadata_str(metadata, "retry_task_id"),
        "presentation_id": new_snapshot.presentation_id,
        "created_at": _utc_now(),
        "sources": _retry_sources(parent_snapshot, new_snapshot, retry_result.events, metadata),
        "plan_snapshot": _plan_snapshot_payload(new_snapshot),
        "render_attempt": _render_attempt_payload(render_result, retry_result.events, retry=True),
        "artifact": _artifact_payload(artifact),
        "event_refs": _event_refs(retry_result.events),
        "retry_links": {
            "parent_task_id": _require_metadata_str(metadata, "parent_task_id"),
            "parent_plan_snapshot_id": parent_snapshot.id,
            "parent_presentation_version_id": parent_snapshot.presentation_version_id,
            "retry_instruction_digest": _require_metadata_str(metadata, "retry_instruction_digest"),
            "new_plan_snapshot_id": new_snapshot.id,
            "new_artifact_id": artifact.id,
        },
        "integrity": {
            "manifest_digest": "",
            "artifact_checksum_sha256": _checksum(render_result),
            "redaction_policy": PROVENANCE_MANIFEST_REDACTION_POLICY,
        },
    }
    return _with_manifest_digest(manifest)


def verify_manifest_digest(manifest: dict[str, Any]) -> bool:
    integrity = manifest.get("integrity")
    if not isinstance(integrity, dict):
        return False
    expected = integrity.get("manifest_digest")
    if not isinstance(expected, str) or not expected.startswith("sha256:"):
        return False
    unsigned = json.loads(json.dumps(manifest))
    unsigned["integrity"]["manifest_digest"] = ""
    return expected == _digest_payload(unsigned)


def _generation_sources(
    plan_snapshot: PresentationPlanSnapshot,
    events: tuple[SlidesTaskEvent, ...],
) -> list[dict[str, object]]:
    return [
        {
            "source_id": plan_snapshot.id,
            "source_kind": "saved_plan_snapshot",
            "role": "approved_plan_snapshot",
            "created_at": _iso(plan_snapshot.created_at),
        },
        {
            "source_id": _event_id_for(events, "slides.render_mode.selected"),
            "source_kind": "render_mode_selection",
            "role": "render_mode_metadata",
            "created_at": _event_created_at_for(events, "slides.render_mode.selected"),
        },
        {
            "source_id": _event_id_for(events, "slides.generation.completed"),
            "source_kind": "task_event_stream",
            "role": "append_only_event_refs",
            "created_at": _event_created_at_for(events, "slides.generation.completed"),
        },
    ]


def _retry_sources(
    parent_snapshot: PresentationPlanSnapshot,
    new_snapshot: PresentationPlanSnapshot,
    events: tuple[SlidesTaskEvent, ...],
    metadata: dict[str, object],
) -> list[dict[str, object]]:
    return [
        {
            "source_id": parent_snapshot.id,
            "source_kind": "saved_plan_snapshot",
            "role": "parent_saved_plan_snapshot",
            "created_at": _iso(parent_snapshot.created_at),
        },
        {
            "source_id": new_snapshot.id,
            "source_kind": "saved_plan_snapshot",
            "role": "new_retry_plan_snapshot",
            "created_at": _iso(new_snapshot.created_at),
        },
        {
            "source_id": _require_metadata_str(metadata, "retry_instruction_digest"),
            "source_kind": "operator_instruction",
            "role": "retry_instruction_digest_only",
            "created_at": _event_created_at_for(events, "slides.retry.from_saved_plan.requested"),
        },
        {
            "source_id": _event_id_for(events, "slides.retry.render_mode.confirmed"),
            "source_kind": "render_mode_selection",
            "role": "render_mode_metadata",
            "created_at": _event_created_at_for(events, "slides.retry.render_mode.confirmed"),
        },
        {
            "source_id": _event_id_for(events, "slides.retry.generation.completed"),
            "source_kind": "task_event_stream",
            "role": "append_only_event_refs",
            "created_at": _event_created_at_for(events, "slides.retry.generation.completed"),
        },
    ]


def _plan_snapshot_payload(snapshot: PresentationPlanSnapshot) -> dict[str, object]:
    payload = snapshot.snapshot_json
    slides = payload.get("slides") if isinstance(payload, dict) else None
    return {
        "plan_snapshot_id": snapshot.id,
        "presentation_id": snapshot.presentation_id,
        "presentation_version_id": snapshot.presentation_version_id,
        "schema_version": int(payload.get("schema_version") or 1),
        "deck_title": str(payload.get("deck_title") or ""),
        "slide_count": len(slides) if isinstance(slides, list) else 0,
    }


def _render_attempt_payload(
    render_result: ApprovedPlanRenderResult,
    events: tuple[SlidesTaskEvent, ...],
    *,
    retry: bool,
) -> dict[str, object]:
    metadata = render_result.safe_metadata
    event_type = "slides.retry.render_mode.confirmed" if retry else "slides.render_mode.selected"
    payload: dict[str, object] = {
        "render_mode": render_result.render_mode,
        "layout_policy": metadata.get("layout_policy") or "unknown_local_layout_policy",
        "template_source": metadata.get("template_source") or "local_builtin_registry",
        "render_event_id": _event_id_for(events, event_type),
        "template_id": render_result.template_id,
        "template_locked": bool(metadata.get("template_locked", False)),
        "external_template_download_allowed": bool(metadata.get("external_template_download_allowed", False)),
        "render_mode_runtime_hardened": bool(metadata.get("render_mode_runtime_hardened", False)),
    }
    return payload


def _artifact_payload(artifact: Artifact) -> dict[str, object]:
    return {
        "artifact_id": artifact.id,
        "filename": artifact.filename,
        "content_type": artifact.content_type,
        "storage_backend": artifact.storage_backend,
        "storage_key": artifact.storage_key,
        "storage_uri": artifact.storage_uri,
        "size_bytes": artifact.size_bytes,
    }


def _event_refs(events: tuple[SlidesTaskEvent, ...]) -> list[dict[str, object]]:
    return [
        {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "created_at": event.created_at,
            "safe_payload": dict(event.safe_payload),
        }
        for event in events
    ]


def _with_manifest_digest(manifest: dict[str, Any]) -> dict[str, Any]:
    finalized = json.loads(json.dumps(manifest, sort_keys=True))
    finalized["integrity"]["manifest_digest"] = _digest_payload(finalized)
    return finalized


def _digest_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(canonical).hexdigest()


def _manifest_bytes(manifest: dict[str, Any]) -> bytes:
    return (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _emission_result(
    *,
    manifest: dict[str, Any],
    content: bytes,
    artifact: Artifact,
    pptx_artifact: Artifact,
    retry: bool,
) -> SlidesProvenanceManifestEmissionResult:
    metadata = {
        "workflow_id": "slides.provenance_manifest_runtime",
        "schema_version": "slides_provenance_manifest_runtime.v1",
        "provenance_manifest_emitted_by_rf2_6": True,
        "provenance_manifest_artifact_registered": True,
        "provenance_manifest_downloadable": True,
        "manifest_artifact_id": artifact.id,
        "manifest_artifact_filename": artifact.filename,
        "manifest_artifact_content_type": artifact.content_type,
        "manifest_size_bytes": artifact.size_bytes,
        "manifest_digest": manifest["integrity"]["manifest_digest"],
        "pptx_artifact_id": pptx_artifact.id,
        "manifest_links_pptx_artifact": manifest["artifact"]["artifact_id"] == pptx_artifact.id,
        "manifest_links_plan_snapshot": bool(manifest.get("plan_snapshot", {}).get("plan_snapshot_id")),
        "manifest_links_render_mode": bool(manifest.get("render_attempt", {}).get("render_mode")),
        "manifest_event_refs_append_only": True,
        "manifest_safe_payload_only": True,
        "retry_manifest": retry,
        "network_required": False,
        "dependency_versions_changed_by_rf2_6": False,
        "dockerfiles_changed_by_rf2_6": False,
        "kimi_grade_supported": False,
        "whole_project_kimi_level_supported": False,
    }
    return SlidesProvenanceManifestEmissionResult(
        manifest=manifest,
        manifest_content=content,
        manifest_artifact=artifact,
        safe_metadata=metadata,
    )


def _assert_manifest_valid(manifest: dict[str, Any], *, retry: bool) -> None:
    errors = validate_manifest_payload(manifest, retry=retry)
    if not verify_manifest_digest(manifest):
        errors.append("manifest digest does not verify")
    if errors:
        raise ValueError("Slides provenance manifest validation failed: " + "; ".join(errors))


def _default_manifest_filename(pptx_filename: str) -> str:
    base = pptx_filename[:-5] if pptx_filename.endswith(".pptx") else pptx_filename
    if not base or "/" in base or "\\" in base or ".." in base:
        base = "slides-artifact"
    return f"{base}.provenance.json"


def _checksum(render_result: ApprovedPlanRenderResult) -> str:
    checksum = render_result.checksum_sha256
    return checksum if checksum.startswith("sha256:") else f"sha256:{checksum}"


def _event_id_for(events: tuple[SlidesTaskEvent, ...], event_type: str) -> str:
    for event in events:
        if event.event_type == event_type:
            return event.event_id
    raise ValueError(f"Missing event for provenance manifest: {event_type}")


def _event_created_at_for(events: tuple[SlidesTaskEvent, ...], event_type: str) -> str:
    for event in events:
        if event.event_type == event_type:
            return event.created_at
    raise ValueError(f"Missing event for provenance manifest: {event_type}")


def _require_metadata_str(metadata: dict[str, object], key: str) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing provenance metadata field: {key}")
    return value


def _iso(value: object) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
