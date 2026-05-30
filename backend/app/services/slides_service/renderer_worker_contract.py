from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any, Literal

from backend.app.services.slides_service.presentation_ir import (
    PRESENTATION_IR_SCHEMA_VERSION,
    require_presentation_ir_payload,
)
from backend.app.services.slides_service.visual_grammar import (
    VISUAL_GRAMMAR_SCHEMA_VERSION,
    PresentationVisualGrammarLibrary,
)

RENDERER_WORKER_CONTRACT_SCHEMA_VERSION = "presentation_renderer_worker_contract.v1"
RENDERER_WORKER_INPUT_SCHEMA_VERSION = "presentation_renderer_worker_input.v1"
RENDERER_WORKER_ARTIFACT_BUNDLE_SCHEMA_VERSION = "presentation_renderer_artifact_bundle.v1"
RENDERER_WORKER_PROOF_BUNDLE_SCHEMA_VERSION = "presentation_renderer_proof_bundle.v1"
RENDERER_WORKER_SOURCE_IMAGE_HARDENING_SCHEMA_VERSION = "presentation_renderer_worker_source_image_hardening.v1"
RENDERER_WORKER_KR7H_CLOSURE_GATE_SCHEMA_VERSION = "presentation_renderer_worker_kr7h_closure_gate.v1"
RENDERER_WORKER_RUNTIME_IMPLEMENTED = False
RENDERER_WORKER_ENGINE = "node_pptxgenjs_worker_contract_only"
RENDERER_WORKER_PROOF_PIPELINE = "libreoffice_pdf_png_proof_contract_only"

RendererWorkerContractStatus = Literal["ready", "blocked"]

FORBIDDEN_RENDERER_ASSET_SOURCES = {
    "ai_generated",
    "external",
    "external_url",
    "fallback",
    "fake",
    "generated",
    "local_deterministic",
    "noop",
    "placeholder",
    "random",
    "synthetic",
    "web",
}

SOURCE_BACKED_ASSET_SOURCES = {
    "document",
    "presentation",
    "source",
    "source_asset",
    "stored_file",
    "uploaded_file",
}

IMAGE_BLOCK_TYPES = {"image", "picture", "source_image", "media_image", "raster_image"}
IMAGE_MIME_PREFIX = "image/"
SOURCE_IMAGE_REF_KEYS = (
    "source_asset_id",
    "source_ref",
    "source_id",
    "source_file_id",
    "source_document_id",
    "provenance_ref",
    "checksum_sha256",
)
INLINE_IMAGE_PAYLOAD_KEYS = ("content_bytes", "bytes", "base64", "data_uri", "inline_data", "image_data")
GENERATED_FLAG_KEYS = (
    "generated",
    "is_generated",
    "ai_generated",
    "fake",
    "is_fake",
    "placeholder",
    "is_placeholder",
    "fallback",
    "uses_fallback",
    "synthetic",
)


@dataclass(frozen=True)
class RendererWorkerContractIssue:
    code: str
    message: str
    path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RendererWorkerContractValidationResult:
    schema_version: str
    status: RendererWorkerContractStatus
    renderer_runtime_implemented: bool
    production_pptx_output_implemented: bool
    proof_bundle_runtime_implemented: bool
    issues: tuple[RendererWorkerContractIssue, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "renderer_runtime_implemented": self.renderer_runtime_implemented,
            "production_pptx_output_implemented": self.production_pptx_output_implemented,
            "proof_bundle_runtime_implemented": self.proof_bundle_runtime_implemented,
            "issues": [issue.as_dict() for issue in self.issues],
        }


def renderer_worker_boundary_contract_payload() -> dict[str, Any]:
    """Return the KR-7H.1 renderer boundary contract without runtime claims.

    KR-7H.1 is a fail-closed preflight contract only. It documents the future
    Python PresentationIR -> Node/PptxGenJS renderer input -> artifact/proof
    bundle boundary, but it does not start a worker, render PPTX, call
    LibreOffice, or claim production-quality output.
    """

    return {
        "schema_version": RENDERER_WORKER_CONTRACT_SCHEMA_VERSION,
        "phase": "KR-7H.1 renderer worker boundary contract preflight",
        "renderer_runtime_implemented": RENDERER_WORKER_RUNTIME_IMPLEMENTED,
        "production_pptx_output_implemented": False,
        "proof_bundle_runtime_implemented": False,
        "input_schema_version": RENDERER_WORKER_INPUT_SCHEMA_VERSION,
        "artifact_bundle_schema_version": RENDERER_WORKER_ARTIFACT_BUNDLE_SCHEMA_VERSION,
        "proof_bundle_schema_version": RENDERER_WORKER_PROOF_BUNDLE_SCHEMA_VERSION,
        "boundary_chain": [
            "python_backend_builds_presentation_ir",
            "node_pptxgenjs_worker_receives_json",
            "pptxgenjs_creates_native_editable_pptx",
            "libreoffice_renders_pdf_png_proof",
            "backend_stores_artifact_and_proof_bundle",
        ],
        "renderer_engine": RENDERER_WORKER_ENGINE,
        "proof_pipeline": RENDERER_WORKER_PROOF_PIPELINE,
        "fail_closed": True,
        "required_input_guards": [
            "presentation_ir_schema_version",
            "slides_have_ids_roles_blocks_and_visual_plan",
            "visual_grammar_blocks_validate_before_render",
            "native_chart_blocks_require_real_numeric_source_data_refs",
            "source_images_only",
            "unsupported_blocks_are_blocked_not_rendered",
        ],
        "declared_artifact_bundle": {
            "schema_version": RENDERER_WORKER_ARTIFACT_BUNDLE_SCHEMA_VERSION,
            "status": "declared_not_produced_by_kr7h1",
            "required_future_artifacts": [
                "editable_pptx",
                "render_report_json",
                "rendered_pdf_proof",
                "rendered_png_slide_proofs",
                "artifact_manifest_json",
            ],
        },
        "declared_proof_bundle": {
            "schema_version": RENDERER_WORKER_PROOF_BUNDLE_SCHEMA_VERSION,
            "status": "declared_not_produced_by_kr7h1",
            "required_future_proofs": ["pdf_proof", "slide_png_proofs", "geometry_report", "quality_gate_report"],
        },
        "source_image_hardening_schema_version": RENDERER_WORKER_SOURCE_IMAGE_HARDENING_SCHEMA_VERSION,
        "source_image_policy": {
            "source_images_only": True,
            "generated_images_allowed": False,
            "fallback_images_allowed": False,
            "fake_artifacts_allowed": False,
            "inline_image_payloads_allowed": False,
            "image_mapping_implemented": False,
            "source_image_selection_implemented": False,
        },
        "non_goals": [
            "no_pptx_rendering_runtime",
            "no_node_worker_execution",
            "no_libreoffice_execution",
            "no_visual_qa_scoring",
            "no_quality_scoring",
            "no_ui_runtime",
            "no_production_quality_output_claims",
        ],
    }


def build_renderer_worker_input_payload(
    presentation_ir: dict[str, Any],
    *,
    request_id: str = "kr7h1_preflight",
) -> dict[str, Any]:
    """Build future renderer-worker input JSON while keeping runtime disabled."""

    validation = validate_renderer_worker_input_payload(presentation_ir)
    return {
        "schema_version": RENDERER_WORKER_INPUT_SCHEMA_VERSION,
        "contract_schema_version": RENDERER_WORKER_CONTRACT_SCHEMA_VERSION,
        "request_id": request_id,
        "renderer_runtime_implemented": RENDERER_WORKER_RUNTIME_IMPLEMENTED,
        "renderer_engine": RENDERER_WORKER_ENGINE,
        "proof_pipeline": RENDERER_WORKER_PROOF_PIPELINE,
        "fail_closed": True,
        "status": validation.status,
        "validation": validation.as_dict(),
        "presentation_ir_schema_version": PRESENTATION_IR_SCHEMA_VERSION,
        "visual_grammar_schema_version": VISUAL_GRAMMAR_SCHEMA_VERSION,
        "artifact_bundle_schema_version": RENDERER_WORKER_ARTIFACT_BUNDLE_SCHEMA_VERSION,
        "proof_bundle_schema_version": RENDERER_WORKER_PROOF_BUNDLE_SCHEMA_VERSION,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
        "presentation_ir": deepcopy(presentation_ir),
    }


def validate_renderer_worker_input_payload(presentation_ir: dict[str, Any]) -> RendererWorkerContractValidationResult:
    issues: list[RendererWorkerContractIssue] = []
    try:
        payload = require_presentation_ir_payload(presentation_ir)
    except Exception as exc:  # noqa: BLE001 - validation must fail closed for any malformed payload
        return _result(
            "blocked",
            [
                RendererWorkerContractIssue(
                    code="invalid_presentation_ir_payload",
                    message=f"PresentationIR is invalid for renderer worker input: {exc}",
                    path="presentation_ir",
                )
            ],
        )

    if payload.get("schema_version") != PRESENTATION_IR_SCHEMA_VERSION:
        issues.append(_issue("unsupported_presentation_ir_schema", "PresentationIR schema_version is unsupported.", "schema_version"))

    slides = payload.get("slides") if isinstance(payload.get("slides"), list) else []
    if not slides:
        issues.append(_issue("missing_slides", "Renderer worker input requires at least one slide.", "slides"))

    quality_contract = payload.get("quality_contract") if isinstance(payload.get("quality_contract"), dict) else {}
    if quality_contract.get("renderer_runtime_implemented") is True:
        issues.append(
            _issue(
                "unsupported_renderer_runtime_claim",
                "KR-7H.1 must not claim renderer runtime implementation in PresentationIR quality_contract.",
                "quality_contract.renderer_runtime_implemented",
            )
        )
    if quality_contract.get("production_pptx_output_implemented") is True:
        issues.append(
            _issue(
                "unsupported_production_output_claim",
                "KR-7H.1 must not claim production PPTX output implementation.",
                "quality_contract.production_pptx_output_implemented",
            )
        )

    if quality_contract.get("source_images_only") is not True:
        issues.append(_issue("source_images_only_not_enforced", "Renderer boundary requires explicit source_images_only=true policy.", "quality_contract.source_images_only"))
    if quality_contract.get("no_generated_images") is not True:
        issues.append(_issue("no_generated_images_not_enforced", "Renderer boundary requires explicit no_generated_images=true policy.", "quality_contract.no_generated_images"))

    _validate_slides(slides, issues)
    _validate_assets(payload.get("assets") or [], issues)
    _validate_visual_grammar_blocks(slides, issues)

    return _result("ready" if not issues else "blocked", issues)


def _validate_slides(slides: list[Any], issues: list[RendererWorkerContractIssue]) -> None:
    for index, slide in enumerate(slides):
        path = f"slides[{index}]"
        if not isinstance(slide, dict):
            issues.append(_issue("slide_must_be_object", "Each renderer input slide must be an object.", path))
            continue
        for key in ("slide_id", "role", "blocks", "visual_plan"):
            if key not in slide:
                issues.append(_issue("missing_renderer_slide_key", f"Renderer input slide is missing {key}.", f"{path}.{key}"))
        if not isinstance(slide.get("blocks"), list):
            issues.append(_issue("slide_blocks_must_be_list", "Renderer input slide.blocks must be a list.", f"{path}.blocks"))
        visual_plan = slide.get("visual_plan")
        if not isinstance(visual_plan, dict):
            issues.append(_issue("slide_visual_plan_must_be_object", "Renderer input slide.visual_plan must be an object.", f"{path}.visual_plan"))
            visual_plan = {}
        if visual_plan.get("requires_image") is True and not _slide_has_source_image_binding(slide):
            issues.append(
                _issue(
                    "source_image_required_but_unbound",
                    "Slide requires an image, but no source-backed image asset/ref is bound; renderer must fail closed instead of inventing an image.",
                    f"{path}.visual_plan.requires_image",
                )
            )


def _validate_assets(assets: list[Any], issues: list[RendererWorkerContractIssue]) -> None:
    for index, asset in enumerate(assets):
        path = f"assets[{index}]"
        if not isinstance(asset, dict):
            issues.append(_issue("asset_must_be_object", "Renderer input asset must be an object.", path))
            continue
        source_kind = _asset_source_kind(asset)
        if source_kind in FORBIDDEN_RENDERER_ASSET_SOURCES:
            issues.append(
                _issue(
                    "non_source_asset_forbidden",
                    "KR-7H.12 renderer hardening allows source-backed assets only; generated, fallback, fake, random, web, or synthetic assets must stay blocked.",
                    path,
                )
            )
        if _has_generated_or_fake_flag(asset):
            issues.append(
                _issue(
                    "fake_or_generated_asset_forbidden",
                    "Renderer input asset carries generated/fake/fallback/placeholder metadata and must not be treated as a success artifact.",
                    path,
                )
            )
        if _asset_is_image(asset):
            if source_kind not in SOURCE_BACKED_ASSET_SOURCES:
                issues.append(
                    _issue(
                        "source_image_asset_source_missing",
                        "Image assets must declare a source-backed source/source_type/asset_source value.",
                        path,
                    )
                )
            if not _has_source_image_ref(asset):
                issues.append(
                    _issue(
                        "source_image_asset_ref_missing",
                        "Image assets must include source asset/ref/checksum provenance before any renderer path may use them.",
                        path,
                    )
                )
            if _has_inline_image_payload(asset):
                issues.append(
                    _issue(
                        "inline_or_placeholder_image_payload_forbidden",
                        "Renderer worker input must not carry inline image bytes/base64/data URIs as proof of a source image.",
                        path,
                    )
                )


def _validate_visual_grammar_blocks(slides: list[Any], issues: list[RendererWorkerContractIssue]) -> None:
    library = PresentationVisualGrammarLibrary()
    known_types = {spec.block_type for spec in library.list_specs()}
    for slide_index, slide in enumerate(slides):
        if not isinstance(slide, dict):
            continue
        for block_index, block in enumerate(slide.get("blocks") or []):
            if not isinstance(block, dict):
                issues.append(_issue("block_must_be_object", "Renderer input block must be an object.", f"slides[{slide_index}].blocks[{block_index}]"))
                continue
            block_type = str(block.get("type") or "")
            binding = block.get("visual_grammar_binding") if isinstance(block.get("visual_grammar_binding"), dict) else None
            block_path = f"slides[{slide_index}].blocks[{block_index}]"
            if _block_is_image_like(block) and not _block_has_source_image_binding(block):
                issues.append(
                    _issue(
                        "source_image_block_ref_missing",
                        "Image-like renderer blocks must be bound to source image refs/assets and must fail closed when unbound.",
                        block_path,
                    )
                )
            if _block_is_image_like(block) and _block_has_forbidden_image_payload(block):
                issues.append(
                    _issue(
                        "fake_or_inline_image_block_forbidden",
                        "Image-like renderer blocks must not use fake/generated/fallback/inline image payloads as success evidence.",
                        block_path,
                    )
                )
            if binding and binding.get("status") == "blocked":
                issues.append(
                    _issue(
                        "visual_grammar_binding_blocked",
                        "Renderer worker input blocks PresentationIR slides with blocked visual grammar bindings instead of rendering them.",
                        f"{block_path}.visual_grammar_binding",
                    )
                )
            if block_type == "native_chart" or block_type in known_types:
                validation = library.validate_block(block)
                if validation.status != "ready":
                    for issue in validation.issues:
                        issues.append(
                            _issue(
                                f"visual_grammar_{issue.code}",
                                issue.message,
                                f"{block_path}.{issue.block_id or block_type}",
                            )
                        )


def renderer_worker_source_image_hardening_payload() -> dict[str, Any]:
    """Return the KR-7H.12 renderer hardening contract payload.

    KR-7H.12 is a guardrail/checker layer. It does not implement source image
    selection, image mapping, visual QA, or production renderer closure. It
    makes unsupported image/fake artifact inputs fail closed before later phases
    can reuse source assets.
    """

    return {
        "schema_version": RENDERER_WORKER_SOURCE_IMAGE_HARDENING_SCHEMA_VERSION,
        "phase": "KR-7H.12 renderer hardening: source-image-only, fail-closed, no fake artifacts",
        "status": "ready",
        "renderer_runtime_implemented": RENDERER_WORKER_RUNTIME_IMPLEMENTED,
        "production_pptx_output_implemented": False,
        "source_image_hardening_implemented": True,
        "source_images_only_enforced": True,
        "generated_images_allowed": False,
        "fallback_images_allowed": False,
        "fake_artifacts_allowed": False,
        "inline_image_payloads_allowed": False,
        "source_image_selection_implemented": False,
        "image_mapping_implemented": False,
        "visual_qa_executed": False,
        "blocked_runtime_actions": [
            "use_generated_images",
            "use_placeholder_images",
            "use_fallback_images_as_success",
            "write_fake_artifact_manifest_entries",
            "treat_inline_image_bytes_as_source_asset",
            "map_charts_tables_images",
            "run_professional_layout_engine",
            "claim_visual_quality_score",
        ],
        "non_goals": [
            "no_source_image_selection_runtime",
            "no_image_mapping_runtime",
            "no_visual_qa_scoring",
            "no_production_renderer_closure",
            "no_frontend_changes",
            "no_gigachat_runtime_changes",
        ],
    }


def renderer_worker_kr7h_closure_gate_payload() -> dict[str, Any]:
    """Return the KR-7H closure-gate contract payload.

    KR-7H.13 closes the native renderer-worker foundation phase only. It
    confirms that KR-7H.1 through KR-7H.12 guardrails/checkers are in place,
    but it does not claim a production renderer service, professional layout,
    visual QA/scoring, Kimi-level quality, source-image selection, or image
    mapping.
    """

    completed_layers = [
        {
            "phase": "KR-7H.1",
            "schema_version": RENDERER_WORKER_CONTRACT_SCHEMA_VERSION,
            "capability": "renderer_boundary_contract",
        },
        {
            "phase": "KR-7H.2",
            "schema_version": "presentation_renderer_worker_dry_run.v1",
            "capability": "dry_run_invocation_manifest",
        },
        {
            "phase": "KR-7H.3",
            "schema_version": "presentation_renderer_worker_protocol_preflight.v1",
            "capability": "node_protocol_preflight",
        },
        {
            "phase": "KR-7H.4",
            "schema_version": "presentation_renderer_worker_package_preflight.v1",
            "capability": "isolated_renderer_worker_package",
        },
        {
            "phase": "KR-7H.5",
            "schema_version": "presentation_renderer_worker_pptxgenjs_capability.v1",
            "capability": "pptxgenjs_dependency_capability",
        },
        {
            "phase": "KR-7H.6",
            "schema_version": "presentation_renderer_worker_pptxgenjs_in_memory_preflight.v1",
            "capability": "pptxgenjs_in_memory_preflight",
        },
        {
            "phase": "KR-7H.7",
            "schema_version": "presentation_renderer_worker_empty_pptx_output_smoke.v1",
            "capability": "temporary_empty_pptx_output_smoke",
        },
        {
            "phase": "KR-7H.8",
            "schema_version": "presentation_renderer_worker_static_slide_output_smoke.v1",
            "capability": "temporary_static_slide_output_smoke",
        },
        {
            "phase": "KR-7H.9",
            "schema_version": "presentation_renderer_worker_minimal_ir_mapping_smoke.v1",
            "capability": "minimal_title_body_ir_mapping_smoke",
        },
        {
            "phase": "KR-7H.10",
            "schema_version": "presentation_renderer_worker_pptx_artifact_bundle.v1",
            "capability": "controlled_pptx_artifact_bundle",
        },
        {
            "phase": "KR-7H.11",
            "schema_version": "presentation_renderer_worker_libreoffice_proof_bundle.v1",
            "capability": "libreoffice_pdf_png_proof_bundle_smoke",
        },
        {
            "phase": "KR-7H.12",
            "schema_version": RENDERER_WORKER_SOURCE_IMAGE_HARDENING_SCHEMA_VERSION,
            "capability": "source_image_only_fail_closed_hardening",
        },
    ]

    return {
        "schema_version": RENDERER_WORKER_KR7H_CLOSURE_GATE_SCHEMA_VERSION,
        "phase": "KR-7H.13 KR-7H closure gate",
        "status": "ready",
        "kr7h_closure_gate_implemented": True,
        "kr7h_phase_closed": True,
        "closed_through_phase": "KR-7H.13",
        "completed_layer_count": len(completed_layers),
        "completed_layers": completed_layers,
        "required_full_runner_step": "29h13-renderer-worker-kr7h-closure-gate-check",
        "required_checker": "scripts/kw_renderer_worker_kr7h_closure_gate_check.py",
        "targeted_checks_required": True,
        "full_runner_required": True,
        "docker_smoke_required": True,
        "remote_verification_required": True,
        "renderer_runtime_implemented": RENDERER_WORKER_RUNTIME_IMPLEMENTED,
        "production_pptx_output_implemented": False,
        "production_renderer_closure_implemented": False,
        "visual_qa_executed": False,
        "visual_quality_score": None,
        "source_image_selection_implemented": False,
        "image_mapping_implemented": False,
        "chart_mapping_implemented": False,
        "table_mapping_implemented": False,
        "theme_mapping_implemented": False,
        "professional_layout_engine_implemented": False,
        "kimi_level_quality_claimed": False,
        "fake_artifacts_allowed": False,
        "fallback_renderer_allowed": False,
        "next_phase": "KR-7I template and brand understanding",
        "blocked_runtime_actions": [
            "start_production_renderer_worker_service",
            "claim_production_renderer_closure",
            "claim_visual_quality_score",
            "claim_kimi_level_output",
            "map_charts_tables_images",
            "select_source_images_for_user_deck",
            "run_professional_layout_engine",
            "change_frontend_ui",
            "change_gigachat_runtime",
        ],
        "non_goals": [
            "no_production_renderer_closure",
            "no_visual_qa_scoring",
            "no_kimi_level_quality_claim",
            "no_source_image_selection_runtime",
            "no_image_mapping_runtime",
            "no_charts_tables_images_mapping",
            "no_template_or_brand_understanding",
            "no_frontend_changes",
            "no_gigachat_runtime_changes",
            "no_docker_deploy_postgres_changes",
        ],
    }


def _asset_source_kind(asset: dict[str, Any]) -> str:
    return str(asset.get("source") or asset.get("source_type") or asset.get("asset_source") or asset.get("provenance_source") or "").strip().lower()


def _asset_is_image(asset: dict[str, Any]) -> bool:
    mime_type = str(asset.get("mime_type") or asset.get("content_type") or "").strip().lower()
    asset_type = str(asset.get("type") or asset.get("asset_type") or asset.get("kind") or "").strip().lower()
    file_type = str(asset.get("file_type") or "").strip().lower()
    return mime_type.startswith(IMAGE_MIME_PREFIX) or "image" in {asset_type, file_type} or file_type in {"png", "jpg", "jpeg", "webp", "gif", "bmp", "svg"}


def _has_source_image_ref(value: dict[str, Any]) -> bool:
    for key in SOURCE_IMAGE_REF_KEYS:
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return True
    source_refs = value.get("source_refs")
    return _non_empty_string_list(source_refs)


def _has_generated_or_fake_flag(value: dict[str, Any]) -> bool:
    for key in GENERATED_FLAG_KEYS:
        if value.get(key) is True:
            return True
    source_kind = _asset_source_kind(value)
    return source_kind in FORBIDDEN_RENDERER_ASSET_SOURCES


def _has_inline_image_payload(value: dict[str, Any]) -> bool:
    for key in INLINE_IMAGE_PAYLOAD_KEYS:
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return True
        if isinstance(candidate, (bytes, bytearray)) and candidate:
            return True
    uri = str(value.get("uri") or value.get("url") or "").strip().lower()
    return uri.startswith("data:")


def _slide_has_source_image_binding(slide: dict[str, Any]) -> bool:
    visual_plan = slide.get("visual_plan") if isinstance(slide.get("visual_plan"), dict) else {}
    for key in ("source_image_refs", "source_asset_refs", "image_source_refs"):
        if _non_empty_string_list(visual_plan.get(key)):
            return True
    for block in slide.get("blocks") or []:
        if isinstance(block, dict) and _block_is_image_like(block) and _block_has_source_image_binding(block):
            return True
    return False


def _block_is_image_like(block: dict[str, Any]) -> bool:
    block_type = str(block.get("type") or "").strip().lower()
    semantic_role = str(block.get("semantic_role") or "").strip().lower()
    return block_type in IMAGE_BLOCK_TYPES or block_type.endswith("_image") or "image" in semantic_role


def _block_has_source_image_binding(block: dict[str, Any]) -> bool:
    if _has_source_image_ref(block):
        return True
    for nested_key in ("content", "data_binding"):
        nested = block.get(nested_key)
        if isinstance(nested, dict) and _has_source_image_ref(nested):
            return True
    return False


def _block_has_forbidden_image_payload(block: dict[str, Any]) -> bool:
    if _has_generated_or_fake_flag(block) or _has_inline_image_payload(block):
        return True
    for nested_key in ("content", "data_binding"):
        nested = block.get(nested_key)
        if isinstance(nested, dict) and (_has_generated_or_fake_flag(nested) or _has_inline_image_payload(nested)):
            return True
    return False


def _non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and any(isinstance(item, str) and item.strip() for item in value)


def _result(status: RendererWorkerContractStatus, issues: list[RendererWorkerContractIssue]) -> RendererWorkerContractValidationResult:
    return RendererWorkerContractValidationResult(
        schema_version=RENDERER_WORKER_CONTRACT_SCHEMA_VERSION,
        status=status,
        renderer_runtime_implemented=RENDERER_WORKER_RUNTIME_IMPLEMENTED,
        production_pptx_output_implemented=False,
        proof_bundle_runtime_implemented=False,
        issues=tuple(issues),
    )


def _issue(code: str, message: str, path: str | None = None) -> RendererWorkerContractIssue:
    return RendererWorkerContractIssue(code=code, message=message, path=path)
