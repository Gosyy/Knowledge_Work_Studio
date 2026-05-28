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
RENDERER_WORKER_RUNTIME_IMPLEMENTED = False
RENDERER_WORKER_ENGINE = "node_pptxgenjs_worker_contract_only"
RENDERER_WORKER_PROOF_PIPELINE = "libreoffice_pdf_png_proof_contract_only"

RendererWorkerContractStatus = Literal["ready", "blocked"]


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

    if quality_contract.get("source_images_only") is False:
        issues.append(_issue("source_images_only_not_enforced", "Renderer boundary requires source_images_only policy.", "quality_contract.source_images_only"))

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
        if not isinstance(slide.get("visual_plan"), dict):
            issues.append(_issue("slide_visual_plan_must_be_object", "Renderer input slide.visual_plan must be an object.", f"{path}.visual_plan"))


def _validate_assets(assets: list[Any], issues: list[RendererWorkerContractIssue]) -> None:
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            issues.append(_issue("asset_must_be_object", "Renderer input asset must be an object.", f"assets[{index}]"))
            continue
        source_kind = str(asset.get("source") or asset.get("source_type") or asset.get("asset_source") or "").lower()
        if source_kind and source_kind not in {"source", "uploaded_file", "stored_file", "source_asset", "document", "presentation"}:
            issues.append(
                _issue(
                    "non_source_asset_forbidden",
                    "KR-7H.1 renderer boundary allows source images only; generated or external assets must stay blocked.",
                    f"assets[{index}]",
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
