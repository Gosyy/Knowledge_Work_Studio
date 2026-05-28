from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from backend.app.services.slides_service.renderer_worker_contract import (
    RENDERER_WORKER_ARTIFACT_BUNDLE_SCHEMA_VERSION,
    RENDERER_WORKER_CONTRACT_SCHEMA_VERSION,
    RENDERER_WORKER_ENGINE,
    RENDERER_WORKER_INPUT_SCHEMA_VERSION,
    RENDERER_WORKER_PROOF_BUNDLE_SCHEMA_VERSION,
    RENDERER_WORKER_PROOF_PIPELINE,
    RENDERER_WORKER_RUNTIME_IMPLEMENTED,
    RendererWorkerContractIssue,
    build_renderer_worker_input_payload,
    validate_renderer_worker_input_payload,
)

RENDERER_WORKER_DRY_RUN_SCHEMA_VERSION = "presentation_renderer_worker_dry_run.v1"
RENDERER_WORKER_INVOCATION_MANIFEST_SCHEMA_VERSION = "presentation_renderer_worker_invocation_manifest.v1"
RENDERER_WORKER_DRY_RUN_IMPLEMENTED = True

RendererWorkerDryRunStatus = Literal["ready", "blocked"]


@dataclass(frozen=True)
class RendererWorkerDryRunResult:
    """Deterministic KR-7H.2 dry-run report for the future renderer worker.

    The dry run intentionally stops before runtime invocation. It validates the
    Python-side PresentationIR -> renderer-worker input boundary and emits an
    invocation manifest that explains what a later Node/PptxGenJS worker would
    receive. It never starts Node, generates PPTX, runs LibreOffice, or produces
    artifact/proof bundles.
    """

    schema_version: str
    status: RendererWorkerDryRunStatus
    request_id: str
    renderer_runtime_implemented: bool
    dry_run_implemented: bool
    artifact_bundle_produced: bool
    proof_bundle_produced: bool
    renderer_input: dict[str, Any] | None
    invocation_manifest: dict[str, Any] | None
    issues: tuple[RendererWorkerContractIssue, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "request_id": self.request_id,
            "renderer_runtime_implemented": self.renderer_runtime_implemented,
            "dry_run_implemented": self.dry_run_implemented,
            "artifact_bundle_produced": self.artifact_bundle_produced,
            "proof_bundle_produced": self.proof_bundle_produced,
            "renderer_input": self.renderer_input,
            "invocation_manifest": self.invocation_manifest,
            "issues": [issue.as_dict() for issue in self.issues],
        }


def renderer_worker_dry_run_capabilities() -> dict[str, Any]:
    """Return KR-7H.2 dry-run capability flags without runtime claims."""

    return {
        "schema_version": RENDERER_WORKER_DRY_RUN_SCHEMA_VERSION,
        "phase": "KR-7H.2 renderer worker dry-run scaffold contract",
        "dry_run_implemented": RENDERER_WORKER_DRY_RUN_IMPLEMENTED,
        "renderer_runtime_implemented": RENDERER_WORKER_RUNTIME_IMPLEMENTED,
        "production_pptx_output_implemented": False,
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
        "renderer_input_schema_version": RENDERER_WORKER_INPUT_SCHEMA_VERSION,
        "invocation_manifest_schema_version": RENDERER_WORKER_INVOCATION_MANIFEST_SCHEMA_VERSION,
        "artifact_bundle_schema_version": RENDERER_WORKER_ARTIFACT_BUNDLE_SCHEMA_VERSION,
        "proof_bundle_schema_version": RENDERER_WORKER_PROOF_BUNDLE_SCHEMA_VERSION,
        "dry_run_chain": [
            "validate_python_presentation_ir",
            "build_renderer_worker_input_json",
            "validate_renderer_worker_input_json",
            "emit_invocation_manifest_without_runtime_execution",
            "block_artifact_and_proof_bundle_production",
        ],
        "blocked_runtime_actions": _blocked_runtime_actions(),
        "non_goals": [
            "no_pptx_rendering_runtime",
            "no_node_worker_execution",
            "no_pptxgenjs_dependency_addition",
            "no_libreoffice_execution",
            "no_artifact_bundle_storage",
            "no_proof_bundle_generation",
            "no_visual_qa_scoring",
            "no_production_quality_output_claims",
        ],
    }


def build_renderer_worker_dry_run_report(
    presentation_ir: dict[str, Any],
    *,
    request_id: str = "kr7h2_dry_run",
) -> RendererWorkerDryRunResult:
    """Validate renderer-worker input and emit a fail-closed dry-run report."""

    validation = validate_renderer_worker_input_payload(presentation_ir)
    if validation.status != "ready":
        return RendererWorkerDryRunResult(
            schema_version=RENDERER_WORKER_DRY_RUN_SCHEMA_VERSION,
            status="blocked",
            request_id=request_id,
            renderer_runtime_implemented=RENDERER_WORKER_RUNTIME_IMPLEMENTED,
            dry_run_implemented=RENDERER_WORKER_DRY_RUN_IMPLEMENTED,
            artifact_bundle_produced=False,
            proof_bundle_produced=False,
            renderer_input=None,
            invocation_manifest=None,
            issues=validation.issues,
        )

    renderer_input = build_renderer_worker_input_payload(presentation_ir, request_id=request_id)
    return RendererWorkerDryRunResult(
        schema_version=RENDERER_WORKER_DRY_RUN_SCHEMA_VERSION,
        status="ready",
        request_id=request_id,
        renderer_runtime_implemented=RENDERER_WORKER_RUNTIME_IMPLEMENTED,
        dry_run_implemented=RENDERER_WORKER_DRY_RUN_IMPLEMENTED,
        artifact_bundle_produced=False,
        proof_bundle_produced=False,
        renderer_input=renderer_input,
        invocation_manifest=build_renderer_worker_invocation_manifest(renderer_input, request_id=request_id),
        issues=(),
    )


def build_renderer_worker_invocation_manifest(
    renderer_input: dict[str, Any],
    *,
    request_id: str = "kr7h2_dry_run",
) -> dict[str, Any]:
    """Describe the future renderer invocation without executing it."""

    return {
        "schema_version": RENDERER_WORKER_INVOCATION_MANIFEST_SCHEMA_VERSION,
        "contract_schema_version": RENDERER_WORKER_CONTRACT_SCHEMA_VERSION,
        "renderer_input_schema_version": renderer_input.get("schema_version"),
        "request_id": request_id,
        "status": "dry_run_ready" if renderer_input.get("status") == "ready" else "blocked",
        "invocation_mode": "dry_run_contract_only",
        "renderer_runtime_implemented": RENDERER_WORKER_RUNTIME_IMPLEMENTED,
        "renderer_engine": RENDERER_WORKER_ENGINE,
        "proof_pipeline": RENDERER_WORKER_PROOF_PIPELINE,
        "would_invoke": {
            "runtime": "node_pptxgenjs_worker",
            "transport": "json_file_or_stdin_contract_only",
            "input_schema_version": RENDERER_WORKER_INPUT_SCHEMA_VERSION,
            "output_contract": RENDERER_WORKER_ARTIFACT_BUNDLE_SCHEMA_VERSION,
            "proof_contract": RENDERER_WORKER_PROOF_BUNDLE_SCHEMA_VERSION,
        },
        "blocked_runtime_actions": _blocked_runtime_actions(),
        "artifact_bundle_produced": False,
        "proof_bundle_produced": False,
        "production_pptx_output_implemented": False,
    }


def require_renderer_worker_dry_run_ready(result: RendererWorkerDryRunResult) -> RendererWorkerDryRunResult:
    """Fail closed when dry-run readiness is not available."""

    if result.status != "ready":
        codes = ", ".join(issue.code for issue in result.issues) or "unknown"
        raise ValueError(f"Renderer worker dry run is blocked: {codes}")
    if result.renderer_runtime_implemented:
        raise ValueError("Renderer worker dry run must not claim renderer runtime implementation.")
    if result.artifact_bundle_produced or result.proof_bundle_produced:
        raise ValueError("Renderer worker dry run must not produce artifact or proof bundles.")
    return result


def _blocked_runtime_actions() -> list[str]:
    return [
        "start_node_worker",
        "import_or_execute_pptxgenjs",
        "generate_editable_pptx",
        "run_libreoffice_pdf_export",
        "render_slide_png_proofs",
        "write_artifact_bundle",
        "write_proof_bundle",
        "claim_visual_quality_score",
    ]
