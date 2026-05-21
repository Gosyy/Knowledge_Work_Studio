from __future__ import annotations

from copy import deepcopy
from typing import Any

SCHEMA_VERSION = "browser_evidence_capture_manifest.v1"
WORKFLOW_ID = "browser_assisted"

REQUIRED_CAPTURE_EVENTS = [
    "browser.navigation_plan.created",
    "browser.navigation.approved",
    "browser.capture.started",
    "browser.capture.completed",
    "evidence.bundle.registered",
    "provenance.evidence.linked",
]

REQUIRED_SLIDES_PROVENANCE_LINK_EVENTS = [
    "slides.plan.snapshot.selected",
    "slides.render_mode.selected",
    "slides.generation.started",
    "artifact.registered",
    "provenance.manifest.registered",
    "provenance.evidence.linked",
]

FORBIDDEN_MARKERS = [
    "BEGIN " "PRIVATE KEY",
    "AWS_SECRET_ACCESS_KEY" "=",
    "OPENAI_API_KEY" "=sk-",
    "GIGACHAT_API_KEY" "=",
    "github" "_pat_",
    "sk-" "proj-",
    "sk-" "live-",
    "xox" "b-",
]

FORBIDDEN_PAYLOAD_KEYS = [
    "authorization",
    "cookie",
    "set-cookie",
    "password",
    "secret",
    "token",
    "api_key",
    "private_key",
    "raw_cookie",
    "raw_cookies",
    "localStorage",
    "sessionStorage",
    "raw_dom",
    "raw_html",
    "raw_screenshot",
    "screenshot_pixels",
]


def _redaction_policy() -> dict[str, Any]:
    return {
        "safe_payload_only": True,
        "forbidden_markers": list(FORBIDDEN_MARKERS),
        "forbidden_payload_keys": list(FORBIDDEN_PAYLOAD_KEYS),
    }


def _base_manifest(mode: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "workflow_id": WORKFLOW_ID,
        "mode": mode,
        "offline_ready": True,
        "browser_policy": "internal_only",
        "approval_required": True,
        "runtime_scope": "contract_only_no_autonomous_agent",
        "redaction_policy": _redaction_policy(),
        "notes": [
            "S8 defines browser-assisted internal evidence metadata only.",
            "It does not create a full browser agent or require internet access.",
            "Future browser runtime must produce evidence bundles by artifact id, not raw page secrets.",
        ],
    }


def build_browser_evidence_manifest(mode: str = "capture") -> dict[str, Any]:
    if mode not in {"capture", "slides_link"}:
        raise ValueError("mode must be capture or slides_link")

    manifest = _base_manifest(mode)
    if mode == "capture":
        manifest.update(
            {
                "event_refs": list(REQUIRED_CAPTURE_EVENTS),
                "provenance_link": {
                    "link_role": "supporting_browser_evidence",
                    "required_for_artifact_history": True,
                    "target_manifest_schema": "slides_provenance_manifest.v1",
                },
                "capture": {
                    "task_id": "task_s8_capture",
                    "session_id": "ses_s8_contract",
                    "capture_id": "bcap_s8_contract",
                    "source": {
                        "source_type": "internal_browser_page",
                        "title": "Internal source page",
                        "url_ref": "internal://knowledge-base/slides-source",
                        "url_policy": "internal_only",
                        "host_classification": "internal",
                        "captured_at": "2026-05-01T00:00:00Z",
                    },
                    "operator_approval": {
                        "required": True,
                        "status": "approved",
                        "approved_by_user_id": "user_local_default",
                        "navigation_plan_id": "browser_nav_plan_s8",
                        "approval_reason": "Capture approved internal evidence for a generated artifact.",
                    },
                    "evidence_bundle": {
                        "artifact_id": "art_browser_evidence_bundle_s8",
                        "filename": "browser-evidence-bundle-s8.json",
                        "content_type": "application/json",
                        "storage_backend": "local",
                        "storage_key": "artifacts/browser-evidence-bundle-s8.json",
                        "integrity": {
                            "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                            "size_bytes": 2048,
                        },
                    },
                },
            }
        )
        return manifest

    manifest.update(
        {
            "event_refs": list(REQUIRED_SLIDES_PROVENANCE_LINK_EVENTS),
            "provenance_link": {
                "link_role": "source_to_artifact_evidence",
                "required_for_artifact_history": True,
                "target_manifest_schema": "slides_provenance_manifest.v1",
            },
            "slides_provenance_link": {
                "presentation_id": "pres_s8_contract",
                "plan_snapshot_id": "plansnap_s8_contract_v1",
                "generated_artifact_id": "art_pptx_s8_contract",
                "provenance_manifest_artifact_id": "art_slides_provenance_s8",
                "render_mode": "adaptive",
                "browser_evidence_artifact_ids": ["art_browser_evidence_bundle_s8"],
                "source_links": [
                    {
                        "source_id": "source_browser_internal_page_s8",
                        "source_type": "browser_evidence_bundle",
                        "artifact_id": "art_browser_evidence_bundle_s8",
                        "role": "supporting_evidence",
                    }
                ],
                "retry_parent": {
                    "is_retry": True,
                    "parent_artifact_id": "art_pptx_s8_contract_v1",
                    "parent_plan_snapshot_id": "plansnap_s8_contract_v1",
                    "retry_reason": "Regenerate from saved plan with captured internal evidence.",
                },
            },
        }
    )
    return manifest


def _payload_without_policy(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _payload_without_policy(item) for key, item in value.items() if key != "redaction_policy"}
    if isinstance(value, list):
        return [_payload_without_policy(item) for item in value]
    return value


def _scan_safe_payload(value: Any, *, forbidden_keys: set[str], forbidden_markers: list[str], errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in forbidden_keys:
                errors.append(f"forbidden evidence payload key leaked: {key}")
            _scan_safe_payload(item, forbidden_keys=forbidden_keys, forbidden_markers=forbidden_markers, errors=errors)
        return
    if isinstance(value, list):
        for item in value:
            _scan_safe_payload(item, forbidden_keys=forbidden_keys, forbidden_markers=forbidden_markers, errors=errors)
        return
    if isinstance(value, str):
        for marker in forbidden_markers:
            if marker and marker in value:
                errors.append(f"forbidden evidence marker leaked: {marker}")


def validate_browser_evidence_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be browser_evidence_capture_manifest.v1")
    if manifest.get("workflow_id") != WORKFLOW_ID:
        errors.append("workflow_id must be browser_assisted")

    mode = manifest.get("mode")
    if mode not in {"capture", "slides_link"}:
        errors.append("mode must be capture or slides_link")

    if manifest.get("offline_ready") is not True:
        errors.append("offline_ready must be true")
    if manifest.get("browser_policy") != "internal_only":
        errors.append("browser_policy must be internal_only")
    if manifest.get("approval_required") is not True:
        errors.append("approval_required must be true")
    if manifest.get("runtime_scope") != "contract_only_no_autonomous_agent":
        errors.append("runtime_scope must be contract_only_no_autonomous_agent")

    provenance_link = manifest.get("provenance_link")
    if not isinstance(provenance_link, dict):
        errors.append("provenance_link is required")
    else:
        if provenance_link.get("target_manifest_schema") != "slides_provenance_manifest.v1":
            errors.append("provenance_link.target_manifest_schema must be slides_provenance_manifest.v1")
        if provenance_link.get("required_for_artifact_history") is not True:
            errors.append("provenance_link.required_for_artifact_history must be true")

    event_refs = manifest.get("event_refs")
    if not isinstance(event_refs, list):
        errors.append("event_refs must be a list")
        event_refs = []

    expected_events = REQUIRED_CAPTURE_EVENTS if mode == "capture" else REQUIRED_SLIDES_PROVENANCE_LINK_EVENTS
    for event_name in expected_events:
        if event_name not in event_refs:
            errors.append(f"missing required event: {event_name}")

    if mode == "capture":
        capture = manifest.get("capture")
        if not isinstance(capture, dict):
            errors.append("capture metadata is required")
        else:
            source = capture.get("source")
            if not isinstance(source, dict):
                errors.append("capture.source is required")
            else:
                if source.get("host_classification") != "internal":
                    errors.append("capture.source.host_classification must be internal")
                if source.get("url_policy") not in {"internal_only", "intranet_only"}:
                    errors.append("capture.source.url_policy must be internal_only or intranet_only")
                if not str(source.get("url_ref", "")).startswith("internal://"):
                    errors.append("capture.source.url_ref must use an internal reference")

            approval = capture.get("operator_approval")
            if not isinstance(approval, dict):
                errors.append("capture.operator_approval is required")
            else:
                if approval.get("required") is not True or approval.get("status") != "approved":
                    errors.append("capture mode requires approved operator_approval")
                if not approval.get("approved_by_user_id"):
                    errors.append("operator_approval.approved_by_user_id is required")

            evidence_bundle = capture.get("evidence_bundle")
            if not isinstance(evidence_bundle, dict):
                errors.append("capture.evidence_bundle is required")
            else:
                if not evidence_bundle.get("artifact_id"):
                    errors.append("capture.evidence_bundle.artifact_id is required")
                if evidence_bundle.get("storage_backend") not in {"local", "s3"}:
                    errors.append("capture.evidence_bundle.storage_backend must be local or s3")
                integrity = evidence_bundle.get("integrity")
                if not isinstance(integrity, dict):
                    errors.append("capture.evidence_bundle.integrity is required")
                else:
                    if not integrity.get("sha256"):
                        errors.append("capture.evidence_bundle.integrity.sha256 is required")
                    if not isinstance(integrity.get("size_bytes"), int):
                        errors.append("capture.evidence_bundle.integrity.size_bytes must be an integer")

    if mode == "slides_link":
        link = manifest.get("slides_provenance_link")
        if not isinstance(link, dict):
            errors.append("slides_provenance_link is required")
        else:
            if not link.get("presentation_id"):
                errors.append("slides_provenance_link.presentation_id is required")
            if not link.get("generated_artifact_id"):
                errors.append("slides_provenance_link.generated_artifact_id is required")
            if not link.get("provenance_manifest_artifact_id"):
                errors.append("slides_provenance_link.provenance_manifest_artifact_id is required")
            if not isinstance(link.get("source_links"), list) or not link.get("source_links"):
                errors.append("slides_provenance_link.source_links is required")
            if not isinstance(link.get("browser_evidence_artifact_ids"), list) or not link.get("browser_evidence_artifact_ids"):
                errors.append("slides_provenance_link.browser_evidence_artifact_ids is required")
            retry_parent = link.get("retry_parent")
            if not isinstance(retry_parent, dict):
                errors.append("slides_provenance_link.retry_parent is required")
            else:
                if retry_parent.get("is_retry") is not True:
                    errors.append("slides_provenance_link.retry_parent.is_retry must be true")
                if not retry_parent.get("parent_plan_snapshot_id"):
                    errors.append("slides_provenance_link.retry_parent.parent_plan_snapshot_id is required")

    redaction_policy = manifest.get("redaction_policy")
    if not isinstance(redaction_policy, dict):
        errors.append("redaction_policy is required")
    else:
        if redaction_policy.get("safe_payload_only") is not True:
            errors.append("redaction_policy.safe_payload_only must be true")
        raw_keys = redaction_policy.get("forbidden_payload_keys", [])
        raw_markers = redaction_policy.get("forbidden_markers", [])
        forbidden_keys = {str(item).lower() for item in raw_keys} if isinstance(raw_keys, list) else set()
        forbidden_markers = [str(item) for item in raw_markers] if isinstance(raw_markers, list) else []
        _scan_safe_payload(
            _payload_without_policy(manifest),
            forbidden_keys=forbidden_keys,
            forbidden_markers=forbidden_markers,
            errors=errors,
        )

    return errors


def build_browser_evidence_report(mode: str = "capture") -> dict[str, Any]:
    manifest = build_browser_evidence_manifest(mode)
    errors = validate_browser_evidence_manifest(manifest)
    return {
        "schema_version": SCHEMA_VERSION,
        "workflow_id": WORKFLOW_ID,
        "mode": mode,
        "status": "ready" if not errors else "error",
        "errors": errors,
        "manifest": deepcopy(manifest),
        "required_capture_events": list(REQUIRED_CAPTURE_EVENTS),
        "required_slides_provenance_link_events": list(REQUIRED_SLIDES_PROVENANCE_LINK_EVENTS),
    }
