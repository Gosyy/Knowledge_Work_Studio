from __future__ import annotations

from typing import Any

VISUAL_QA_WORKFLOW_ID = "visual_qa_planning"
VISUAL_QA_SCHEMA_VERSION = "visual_qa_planning_manifest.v1"

VISUAL_QA_REQUIRED_EVENTS = (
    "visual_qa.plan.requested",
    "visual_qa.source_artifacts.selected",
    "visual_qa.checks.selected",
    "visual_qa.plan.registered",
    "provenance.visual_qa_plan.linked",
)

VISUAL_QA_REQUIRED_CHECKS = (
    "artifact_integrity",
    "source_to_artifact_provenance",
    "layout_consistency",
    "text_overflow_risk",
    "reading_order_risk",
    "contrast_risk",
)

VISUAL_QA_ALLOWED_SOURCE_TYPES = (
    "pptx_artifact",
    "pdf_artifact",
    "browser_evidence_bundle",
    "image_artifact_reference",
)

VISUAL_QA_FORBIDDEN_PAYLOAD_KEYS = (
    "authorization",
    "cookie",
    "set-cookie",
    "password",
    "secret",
    "token",
    "api_key",
    "private_key",
    "raw_image",
    "raw_screenshot",
    "screenshot_pixels",
    "raw_pixels",
    "raw_dom",
    "raw_html",
    "raw_ocr_text",
    "external_url",
    "external_visual_api",
)

VISUAL_QA_FORBIDDEN_MARKERS = (
    "BEGIN" + " PRIVATE KEY",
    "AWS" + "_SECRET_ACCESS_KEY=",
    "OPENAI" + "_API_KEY=" + "sk-",
    "GIGACHAT" + "_API_KEY=",
    "github" + "_pat_",
    "sk" + "-proj-",
    "sk" + "-live-",
    "xo" + "xb-",
)


def visual_qa_contract() -> dict[str, Any]:
    return {
        "schema_version": VISUAL_QA_SCHEMA_VERSION,
        "workflow_id": VISUAL_QA_WORKFLOW_ID,
        "title": "Optional multimodal and visual QA planning contract",
        "offline_ready": True,
        "browser_policy": "none",
        "approval_required": True,
        "runtime_scope": "contract_only_no_multimodal_runtime",
        "visual_runtime_required": False,
        "external_model_allowed": False,
        "internet_required": False,
        "server_2_heavy_runtime_optional": True,
        "allowed_source_types": list(VISUAL_QA_ALLOWED_SOURCE_TYPES),
        "required_checks": list(VISUAL_QA_REQUIRED_CHECKS),
        "required_events": list(VISUAL_QA_REQUIRED_EVENTS),
        "non_goals": [
            "No OCR, vision model, screenshot parser, or multimodal runtime is implemented in S10.",
            "No external visual API, cloud OCR, or internet dependency is introduced in S10.",
            "No autonomous browser runtime expansion is introduced in S10.",
            "No generated artifact is rejected automatically without operator review.",
        ],
        "redaction_policy": {
            "safe_payload_only": True,
            "forbidden_payload_keys": list(VISUAL_QA_FORBIDDEN_PAYLOAD_KEYS),
            "forbidden_markers": list(VISUAL_QA_FORBIDDEN_MARKERS),
        },
    }


def build_visual_qa_plan_manifest(mode: str = "slides") -> dict[str, Any]:
    if mode not in {"slides", "artifact"}:
        raise ValueError(f"unsupported visual QA mode: {mode}")

    source_type = "pptx_artifact" if mode == "slides" else "pdf_artifact"
    generated_artifact_id = "art_pptx_s10_contract" if mode == "slides" else "art_pdf_s10_contract"
    plan_id = "visual_qa_plan_slides_s10" if mode == "slides" else "visual_qa_plan_artifact_s10"

    return {
        "schema_version": VISUAL_QA_SCHEMA_VERSION,
        "workflow_id": VISUAL_QA_WORKFLOW_ID,
        "mode": mode,
        "offline_ready": True,
        "browser_policy": "none",
        "approval_required": True,
        "runtime_scope": "contract_only_no_multimodal_runtime",
        "visual_runtime_required": False,
        "external_model_allowed": False,
        "internet_required": False,
        "server_2_heavy_runtime_optional": True,
        "plan": {
            "visual_qa_plan_id": plan_id,
            "generated_artifact_id": generated_artifact_id,
            "source_artifacts": [
                {
                    "artifact_id": generated_artifact_id,
                    "source_type": source_type,
                    "role": "primary_visual_qa_target",
                    "artifact_version": "v1",
                }
            ],
            "checks": [
                {
                    "check_id": check_id,
                    "status": "planned",
                    "requires_runtime": False,
                    "operator_review_required": True,
                }
                for check_id in VISUAL_QA_REQUIRED_CHECKS
            ],
            "evidence_policy": {
                "store_artifact_references_only": True,
                "raw_pixels_allowed": False,
                "raw_ocr_text_allowed": False,
                "external_url_fetch_allowed": False,
            },
            "provenance_link": {
                "required_for_artifact_history": True,
                "link_role": "visual_qa_plan",
                "target_artifact_id": generated_artifact_id,
            },
        },
        "event_refs": list(VISUAL_QA_REQUIRED_EVENTS),
        "redaction_policy": {
            "safe_payload_only": True,
            "forbidden_payload_keys": list(VISUAL_QA_FORBIDDEN_PAYLOAD_KEYS),
            "forbidden_markers": list(VISUAL_QA_FORBIDDEN_MARKERS),
        },
        "notes": [
            "S10 defines visual QA planning metadata only.",
            "Future OCR or multimodal QA runtime must run offline or on Server 2 heavy-node modules.",
            "The plan stores artifact references, not raw screenshots, raw pixels, or raw OCR text.",
        ],
    }


def _payload_without_policy(value: object) -> object:
    if isinstance(value, dict):
        return {key: _payload_without_policy(item) for key, item in value.items() if key != "redaction_policy"}
    if isinstance(value, list):
        return [_payload_without_policy(item) for item in value]
    return value


def validate_visual_qa_plan_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def add(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    def is_dict(value: object) -> bool:
        return isinstance(value, dict)

    add(manifest.get("schema_version") == VISUAL_QA_SCHEMA_VERSION, "schema_version must be visual_qa_planning_manifest.v1")
    add(manifest.get("workflow_id") == VISUAL_QA_WORKFLOW_ID, "workflow_id must be visual_qa_planning")
    add(manifest.get("mode") in {"slides", "artifact"}, "mode must be slides or artifact")
    add(manifest.get("offline_ready") is True, "offline_ready must be true")
    add(manifest.get("browser_policy") == "none", "browser_policy must be none")
    add(manifest.get("approval_required") is True, "approval_required must be true")
    add(manifest.get("runtime_scope") == "contract_only_no_multimodal_runtime", "runtime_scope must be contract_only_no_multimodal_runtime")
    add(manifest.get("visual_runtime_required") is False, "visual_runtime_required must be false in S10")
    add(manifest.get("external_model_allowed") is False, "external_model_allowed must be false")
    add(manifest.get("internet_required") is False, "internet_required must be false")
    add(manifest.get("server_2_heavy_runtime_optional") is True, "server_2 heavy runtime must be optional")

    event_refs = manifest.get("event_refs")
    if isinstance(event_refs, list):
        for event_name in VISUAL_QA_REQUIRED_EVENTS:
            add(event_name in event_refs, f"missing event_ref: {event_name}")
    else:
        errors.append("event_refs must be a list")

    plan = manifest.get("plan")
    if is_dict(plan):
        add(bool(plan.get("visual_qa_plan_id")), "plan.visual_qa_plan_id is required")
        add(bool(plan.get("generated_artifact_id")), "plan.generated_artifact_id is required")
        source_artifacts = plan.get("source_artifacts")
        if isinstance(source_artifacts, list) and source_artifacts:
            for source in source_artifacts:
                if is_dict(source):
                    add(bool(source.get("artifact_id")), "source artifact_id is required")
                    add(source.get("source_type") in VISUAL_QA_ALLOWED_SOURCE_TYPES, "source.source_type must be an allowed artifact reference type")
                else:
                    errors.append("source artifact entries must be objects")
        else:
            errors.append("plan.source_artifacts must include at least one artifact reference")

        checks = plan.get("checks")
        if isinstance(checks, list):
            check_ids = {str(check.get("check_id")) for check in checks if isinstance(check, dict)}
            for check_id in VISUAL_QA_REQUIRED_CHECKS:
                add(check_id in check_ids, f"missing planned visual QA check: {check_id}")
            for check in checks:
                if is_dict(check):
                    add(check.get("requires_runtime") is False, "S10 checks must be planning-only and require no runtime")
                    add(check.get("operator_review_required") is True, "visual QA checks must require operator review")
                else:
                    errors.append("visual QA check entries must be objects")
        else:
            errors.append("plan.checks must be a list")

        evidence_policy = plan.get("evidence_policy")
        if is_dict(evidence_policy):
            add(evidence_policy.get("store_artifact_references_only") is True, "evidence_policy must store artifact references only")
            add(evidence_policy.get("raw_pixels_allowed") is False, "raw pixels must not be allowed")
            add(evidence_policy.get("raw_ocr_text_allowed") is False, "raw OCR text must not be allowed")
            add(evidence_policy.get("external_url_fetch_allowed") is False, "external URL fetch must not be allowed")
        else:
            errors.append("plan.evidence_policy must be present")

        provenance_link = plan.get("provenance_link")
        if is_dict(provenance_link):
            add(provenance_link.get("required_for_artifact_history") is True, "visual QA provenance link must be required for artifact history")
            add(provenance_link.get("link_role") == "visual_qa_plan", "visual QA provenance link_role must be visual_qa_plan")
        else:
            errors.append("plan.provenance_link must be present")
    else:
        errors.append("plan must be present")

    redaction_policy = manifest.get("redaction_policy")
    forbidden_keys: set[str] = set()
    forbidden_markers: list[str] = []
    if is_dict(redaction_policy):
        add(redaction_policy.get("safe_payload_only") is True, "redaction_policy.safe_payload_only must be true")
        raw_keys = redaction_policy.get("forbidden_payload_keys")
        raw_markers = redaction_policy.get("forbidden_markers")
        if isinstance(raw_keys, list):
            forbidden_keys = {str(key).lower() for key in raw_keys}
        else:
            errors.append("redaction_policy.forbidden_payload_keys must be a list")
        if isinstance(raw_markers, list):
            forbidden_markers = [str(marker) for marker in raw_markers if str(marker)]
        else:
            errors.append("redaction_policy.forbidden_markers must be a list")
    else:
        errors.append("redaction_policy must be present")

    payload = _payload_without_policy(manifest)

    def scan(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower() in forbidden_keys:
                    errors.append(f"forbidden visual QA payload key leaked: {key}")
                scan(item)
            return
        if isinstance(value, list):
            for item in value:
                scan(item)
            return
        if isinstance(value, str):
            for marker in forbidden_markers:
                if marker in value:
                    errors.append(f"forbidden visual QA marker leaked: {marker}")

    scan(payload)
    return errors


def build_visual_qa_report(mode: str = "slides") -> dict[str, Any]:
    manifest = build_visual_qa_plan_manifest(mode)
    errors = validate_visual_qa_plan_manifest(manifest)
    return {
        "schema_version": VISUAL_QA_SCHEMA_VERSION,
        "workflow_id": VISUAL_QA_WORKFLOW_ID,
        "mode": mode,
        "status": "ready" if not errors else "error",
        "errors": errors,
        "manifest": manifest,
        "contract": visual_qa_contract(),
        "required_events": list(VISUAL_QA_REQUIRED_EVENTS),
        "required_checks": list(VISUAL_QA_REQUIRED_CHECKS),
    }
