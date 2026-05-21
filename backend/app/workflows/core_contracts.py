from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


WORKFLOW_CONTRACT_CORE_VERSION = "kr4a.workflow_contract_core.v1"

MANDATORY_PRODUCT_WORKFLOW_IDS = (
    "docx",
    "pdf",
    "xlsx",
    "slides",
    "python_analysis",
    "browser_evidence",
)

DEFAULT_REQUIRED_MANIFESTS = (
    "artifact_manifest.json",
    "quality_report.json",
    "source_evidence_manifest.json",
)


@dataclass(frozen=True)
class WorkflowInput:
    workflow_id: str
    source_kinds: tuple[str, ...]
    user_intent_required: bool
    destructive_changes_require_approval: bool
    offline_input_ready: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowPlan:
    workflow_id: str
    plan_artifact: str
    operator_editable: bool
    approval_gate: str
    deterministic_steps: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowRun:
    workflow_id: str
    controlled_tools: tuple[str, ...]
    offline_ready: bool
    local_llm_policy: str
    browser_policy: str
    failure_modes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowArtifact:
    name: str
    kind: str
    required: bool
    provenance_required: bool
    quality_gate: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowManifest:
    workflow_id: str
    manifest_name: str
    required_manifest_files: tuple[str, ...]
    records_artifact_history: bool
    records_restore_metadata: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowQualityReport:
    workflow_id: str
    report_name: str
    required_checks: tuple[str, ...]
    must_fail_closed: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowProvenance:
    workflow_id: str
    source_evidence_manifest: str
    citation_manifest: str | None
    evidence_required: bool
    traceability_level: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowContractCore:
    workflow_id: str
    title: str
    workflow_input: WorkflowInput
    plan: WorkflowPlan
    run: WorkflowRun
    artifacts: tuple[WorkflowArtifact, ...]
    manifest: WorkflowManifest
    quality: WorkflowQualityReport
    provenance: WorkflowProvenance

    def as_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "title": self.title,
            "workflow_input": self.workflow_input.as_dict(),
            "plan": self.plan.as_dict(),
            "run": self.run.as_dict(),
            "artifacts": [artifact.as_dict() for artifact in self.artifacts],
            "manifest": self.manifest.as_dict(),
            "quality": self.quality.as_dict(),
            "provenance": self.provenance.as_dict(),
        }


def _artifact(name: str, kind: str, quality_gate: str, *, provenance_required: bool = True) -> WorkflowArtifact:
    return WorkflowArtifact(
        name=name,
        kind=kind,
        required=True,
        provenance_required=provenance_required,
        quality_gate=quality_gate,
    )


def _manifest(workflow_id: str, *extra_files: str) -> WorkflowManifest:
    required_files = tuple(dict.fromkeys(DEFAULT_REQUIRED_MANIFESTS + tuple(extra_files)))
    return WorkflowManifest(
        workflow_id=workflow_id,
        manifest_name="artifact_manifest.json",
        required_manifest_files=required_files,
        records_artifact_history=True,
        records_restore_metadata=True,
    )


def _provenance(workflow_id: str, *, citation_manifest: str | None = None, traceability_level: str = "source_to_artifact") -> WorkflowProvenance:
    return WorkflowProvenance(
        workflow_id=workflow_id,
        source_evidence_manifest="source_evidence_manifest.json",
        citation_manifest=citation_manifest,
        evidence_required=True,
        traceability_level=traceability_level,
    )


WORKFLOW_CONTRACT_CORE: dict[str, WorkflowContractCore] = {
    "docx": WorkflowContractCore(
        workflow_id="docx",
        title="DOCX document workflow contract",
        workflow_input=WorkflowInput(
            workflow_id="docx",
            source_kinds=("docx", "instruction", "optional_reference_document"),
            user_intent_required=True,
            destructive_changes_require_approval=True,
            offline_input_ready=True,
        ),
        plan=WorkflowPlan(
            workflow_id="docx",
            plan_artifact="docx_workflow_plan.json",
            operator_editable=True,
            approval_gate="destructive_document_edits_require_operator_approval",
            deterministic_steps=("extract_structure", "plan_transform", "generate_docx", "validate_docx"),
        ),
        run=WorkflowRun(
            workflow_id="docx",
            controlled_tools=("python-docx", "document_structure_extractor"),
            offline_ready=True,
            local_llm_policy="local_gigachat_optional_for_text_planning",
            browser_policy="none",
            failure_modes=("unreadable_docx", "unsupported_embedded_object", "validation_failed"),
        ),
        artifacts=(
            _artifact("document.docx", "docx", "docx_opens_and_structure_preserved"),
            _artifact("docx_analysis_report.json", "analysis_report", "docx_analysis_schema_valid"),
            _artifact("source_evidence_manifest.json", "provenance_manifest", "source_evidence_present"),
            _artifact("artifact_manifest.json", "artifact_manifest", "artifact_bundle_complete"),
            _artifact("quality_report.json", "quality_report", "quality_report_ready"),
        ),
        manifest=_manifest("docx", "docx_analysis_report.json"),
        quality=WorkflowQualityReport(
            workflow_id="docx",
            report_name="quality_report.json",
            required_checks=("docx_opens", "structure_preserved", "destructive_edits_not_silent"),
            must_fail_closed=True,
        ),
        provenance=_provenance("docx"),
    ),
    "pdf": WorkflowContractCore(
        workflow_id="pdf",
        title="PDF evidence workflow contract",
        workflow_input=WorkflowInput(
            workflow_id="pdf",
            source_kinds=("pdf", "instruction", "optional_page_range"),
            user_intent_required=True,
            destructive_changes_require_approval=False,
            offline_input_ready=True,
        ),
        plan=WorkflowPlan(
            workflow_id="pdf",
            plan_artifact="pdf_workflow_plan.json",
            operator_editable=True,
            approval_gate="low_confidence_extraction_requires_operator_review",
            deterministic_steps=("extract_text", "render_pages_when_needed", "collect_evidence", "generate_report"),
        ),
        run=WorkflowRun(
            workflow_id="pdf",
            controlled_tools=("pypdf", "pdf_renderer", "table_detector_optional"),
            offline_ready=True,
            local_llm_policy="local_gigachat_optional_for_summarization",
            browser_policy="none",
            failure_modes=("encrypted_pdf", "image_only_pdf_without_ocr", "render_failed"),
        ),
        artifacts=(
            _artifact("pdf_analysis_report.json", "analysis_report", "pdf_analysis_schema_valid"),
            _artifact("page_render_manifest.json", "render_manifest", "render_manifest_ready"),
            _artifact("source_evidence_manifest.json", "provenance_manifest", "source_evidence_present"),
            _artifact("artifact_manifest.json", "artifact_manifest", "artifact_bundle_complete"),
            _artifact("quality_report.json", "quality_report", "quality_report_ready"),
        ),
        manifest=_manifest("pdf", "pdf_analysis_report.json", "page_render_manifest.json"),
        quality=WorkflowQualityReport(
            workflow_id="pdf",
            report_name="quality_report.json",
            required_checks=("pdf_readable_or_failure_explicit", "page_references_preserved", "evidence_snippets_traceable"),
            must_fail_closed=True,
        ),
        provenance=_provenance("pdf", traceability_level="page_or_evidence_snippet_to_artifact"),
    ),
    "xlsx": WorkflowContractCore(
        workflow_id="xlsx",
        title="XLSX and spreadsheet workflow contract",
        workflow_input=WorkflowInput(
            workflow_id="xlsx",
            source_kinds=("xlsx", "csv", "instruction", "optional_chart_request"),
            user_intent_required=True,
            destructive_changes_require_approval=True,
            offline_input_ready=True,
        ),
        plan=WorkflowPlan(
            workflow_id="xlsx",
            plan_artifact="xlsx_workflow_plan.json",
            operator_editable=True,
            approval_gate="destructive_workbook_edits_require_operator_approval",
            deterministic_steps=("inspect_workbook", "inventory_formulas", "export_table_previews", "validate_workbook"),
        ),
        run=WorkflowRun(
            workflow_id="xlsx",
            controlled_tools=("openpyxl", "csv", "libreoffice_calc_optional_validation"),
            offline_ready=True,
            local_llm_policy="local_gigachat_optional_for_analysis_narrative",
            browser_policy="none",
            failure_modes=("malformed_workbook", "unsupported_formula", "destructive_edit_not_approved"),
        ),
        artifacts=(
            _artifact("workbook.xlsx", "xlsx", "workbook_opens"),
            _artifact("workbook_manifest.json", "workbook_manifest", "workbook_manifest_ready"),
            _artifact("xlsx_analysis_report.json", "analysis_report", "xlsx_analysis_schema_valid"),
            _artifact("formula_inventory.json", "formula_inventory", "formulas_inventoried"),
            _artifact("table_previews/*.csv", "table_preview", "table_ranges_traceable"),
            _artifact("source_evidence_manifest.json", "provenance_manifest", "source_ranges_traceable"),
            _artifact("artifact_manifest.json", "artifact_manifest", "artifact_bundle_complete"),
            _artifact("quality_report.json", "quality_report", "quality_report_ready"),
        ),
        manifest=_manifest("xlsx", "workbook_manifest.json", "xlsx_analysis_report.json", "formula_inventory.json"),
        quality=WorkflowQualityReport(
            workflow_id="xlsx",
            report_name="quality_report.json",
            required_checks=("workbook_opens", "sheets_preserved", "formulas_inventoried", "destructive_edits_not_silent"),
            must_fail_closed=True,
        ),
        provenance=_provenance("xlsx", traceability_level="workbook_range_to_artifact"),
    ),
    "slides": WorkflowContractCore(
        workflow_id="slides",
        title="Slides outline-first workflow contract",
        workflow_input=WorkflowInput(
            workflow_id="slides",
            source_kinds=("instruction", "source_files", "optional_template_pptx"),
            user_intent_required=True,
            destructive_changes_require_approval=False,
            offline_input_ready=True,
        ),
        plan=WorkflowPlan(
            workflow_id="slides",
            plan_artifact="slide_plan.json",
            operator_editable=True,
            approval_gate="outline_plan_review_before_generation",
            deterministic_steps=("create_outline", "review_plan", "generate_pptx", "render_qa", "visual_qa"),
        ),
        run=WorkflowRun(
            workflow_id="slides",
            controlled_tools=("python-pptx", "libreoffice_impress", "poppler_pdftoppm", "visual_qa"),
            offline_ready=True,
            local_llm_policy="local_gigachat_default_for_narrative_planning",
            browser_policy="none",
            failure_modes=("unsupported_template", "render_failed", "visual_qa_failed", "unsupported_claim"),
        ),
        artifacts=(
            _artifact("deck.pptx", "pptx", "pptx_opens"),
            _artifact("rendered_slides/*.png", "rendered_slide", "primary_render_ready"),
            _artifact("independent_rendered_slides/*.png", "independent_rendered_slide", "independent_render_ready"),
            _artifact("slide_plan.json", "workflow_plan", "slide_plan_schema_valid"),
            _artifact("citation_manifest.json", "citation_manifest", "citation_coverage_ready"),
            _artifact("source_evidence_manifest.json", "provenance_manifest", "source_evidence_present"),
            _artifact("geometry_report.json", "geometry_report", "geometry_report_ready"),
            _artifact("visual_qa_report.json", "visual_qa_report", "visual_qa_ready"),
            _artifact("review_packet.json", "review_packet", "operator_review_packet_ready"),
            _artifact("artifact_manifest.json", "artifact_manifest", "artifact_bundle_complete"),
        ),
        manifest=_manifest(
            "slides",
            "slide_plan.json",
            "citation_manifest.json",
            "geometry_report.json",
            "visual_qa_report.json",
            "review_packet.json",
        ),
        quality=WorkflowQualityReport(
            workflow_id="slides",
            report_name="visual_qa_report.json",
            required_checks=("pptx_opens", "independent_render_ready", "visual_qa_ready", "citation_coverage_checked"),
            must_fail_closed=True,
        ),
        provenance=_provenance("slides", citation_manifest="citation_manifest.json", traceability_level="claim_to_source_evidence"),
    ),
    "python_analysis": WorkflowContractCore(
        workflow_id="python_analysis",
        title="Controlled Python analysis workflow contract",
        workflow_input=WorkflowInput(
            workflow_id="python_analysis",
            source_kinds=("csv", "xlsx", "json", "instruction", "approved_python"),
            user_intent_required=True,
            destructive_changes_require_approval=False,
            offline_input_ready=True,
        ),
        plan=WorkflowPlan(
            workflow_id="python_analysis",
            plan_artifact="analysis_plan.json",
            operator_editable=True,
            approval_gate="operator_review_for_code_execution",
            deterministic_steps=("prepare_inputs", "execute_controlled_python", "export_tables", "export_plots", "write_report"),
        ),
        run=WorkflowRun(
            workflow_id="python_analysis",
            controlled_tools=("python_runtime", "pandas_optional", "matplotlib_optional"),
            offline_ready=True,
            local_llm_policy="local_gigachat_optional_for_explanation_only",
            browser_policy="none",
            failure_modes=("execution_timeout", "missing_dependency", "unapproved_code_path"),
        ),
        artifacts=(
            _artifact("analysis.py", "script", "script_recorded"),
            _artifact("analysis_report.md", "markdown_report", "analysis_report_ready"),
            _artifact("analysis_results.json", "analysis_results", "analysis_results_schema_valid"),
            _artifact("tables/*.csv", "table_export", "table_exports_traceable"),
            _artifact("plots/*.png", "plot_export", "plot_exports_traceable"),
            _artifact("execution_log.txt", "execution_log", "execution_log_recorded"),
            _artifact("artifact_manifest.json", "artifact_manifest", "artifact_bundle_complete"),
            _artifact("quality_report.json", "quality_report", "quality_report_ready"),
            _artifact("source_evidence_manifest.json", "provenance_manifest", "source_evidence_present"),
        ),
        manifest=_manifest("python_analysis", "analysis_results.json", "execution_log.txt"),
        quality=WorkflowQualityReport(
            workflow_id="python_analysis",
            report_name="quality_report.json",
            required_checks=("execution_logged", "outputs_exist", "inputs_traceable", "reproducibility_metadata_present"),
            must_fail_closed=True,
        ),
        provenance=_provenance("python_analysis", traceability_level="input_dataset_to_output_artifact"),
    ),
    "browser_evidence": WorkflowContractCore(
        workflow_id="browser_evidence",
        title="Browser-assisted evidence workflow contract",
        workflow_input=WorkflowInput(
            workflow_id="browser_evidence",
            source_kinds=("approved_internal_url", "user_provided_page", "instruction"),
            user_intent_required=True,
            destructive_changes_require_approval=False,
            offline_input_ready=True,
        ),
        plan=WorkflowPlan(
            workflow_id="browser_evidence",
            plan_artifact="browser_capture_plan.json",
            operator_editable=True,
            approval_gate="operator_approval_for_navigation_scope",
            deterministic_steps=("approve_scope", "capture_pages", "capture_screenshots", "write_evidence_manifest"),
        ),
        run=WorkflowRun(
            workflow_id="browser_evidence",
            controlled_tools=("playwright_or_cdp_runtime", "screenshot_capture", "html_text_capture"),
            offline_ready=True,
            local_llm_policy="local_gigachat_optional_for_evidence_summary",
            browser_policy="approved_internal_or_user_provided_only",
            failure_modes=("navigation_not_approved", "page_capture_failed", "screenshot_failed"),
        ),
        artifacts=(
            _artifact("browser_evidence_manifest.json", "browser_evidence_manifest", "browser_evidence_manifest_ready"),
            _artifact("screenshots/*.png", "screenshot", "screenshots_recorded"),
            _artifact("captured_pages/*.html", "captured_page", "captured_pages_recorded"),
            _artifact("source_evidence_manifest.json", "provenance_manifest", "source_evidence_present"),
            _artifact("quality_report.json", "quality_report", "quality_report_ready"),
            _artifact("artifact_manifest.json", "artifact_manifest", "artifact_bundle_complete"),
        ),
        manifest=_manifest("browser_evidence", "browser_evidence_manifest.json"),
        quality=WorkflowQualityReport(
            workflow_id="browser_evidence",
            report_name="quality_report.json",
            required_checks=("navigation_scope_approved", "screenshots_recorded", "page_metadata_recorded", "evidence_manifest_ready"),
            must_fail_closed=True,
        ),
        provenance=_provenance("browser_evidence", traceability_level="captured_page_to_output_artifact"),
    ),
}


def list_workflow_contract_core() -> tuple[WorkflowContractCore, ...]:
    return tuple(WORKFLOW_CONTRACT_CORE[workflow_id] for workflow_id in MANDATORY_PRODUCT_WORKFLOW_IDS)


def get_workflow_contract_core(workflow_id: str) -> WorkflowContractCore:
    return WORKFLOW_CONTRACT_CORE[workflow_id]


def workflow_contract_core_report() -> dict[str, Any]:
    errors = validate_workflow_contract_core()
    return {
        "schema_version": WORKFLOW_CONTRACT_CORE_VERSION,
        "status": "ready" if not errors else "not_ready",
        "mandatory_product_workflow_ids": list(MANDATORY_PRODUCT_WORKFLOW_IDS),
        "workflow_count": len(WORKFLOW_CONTRACT_CORE),
        "contracts": {workflow_id: contract.as_dict() for workflow_id, contract in WORKFLOW_CONTRACT_CORE.items()},
        "errors": errors,
    }


def _artifact_names(contract: WorkflowContractCore) -> set[str]:
    return {artifact.name for artifact in contract.artifacts}


def _manifest_files(contract: WorkflowContractCore) -> set[str]:
    return set(contract.manifest.required_manifest_files)


def validate_workflow_contract_core() -> list[str]:
    errors: list[str] = []
    missing = [workflow_id for workflow_id in MANDATORY_PRODUCT_WORKFLOW_IDS if workflow_id not in WORKFLOW_CONTRACT_CORE]
    if missing:
        errors.append("missing workflow contract core(s): " + ", ".join(missing))

    extra = sorted(set(WORKFLOW_CONTRACT_CORE) - set(MANDATORY_PRODUCT_WORKFLOW_IDS))
    if extra:
        errors.append("unexpected workflow contract core(s): " + ", ".join(extra))

    for workflow_id, contract in WORKFLOW_CONTRACT_CORE.items():
        if contract.workflow_id != workflow_id:
            errors.append(f"{workflow_id}: workflow_id field mismatch")
        nested_ids = (
            contract.workflow_input.workflow_id,
            contract.plan.workflow_id,
            contract.run.workflow_id,
            contract.manifest.workflow_id,
            contract.quality.workflow_id,
            contract.provenance.workflow_id,
        )
        if any(nested_id != workflow_id for nested_id in nested_ids):
            errors.append(f"{workflow_id}: nested contract workflow_id mismatch")
        if not contract.workflow_input.user_intent_required:
            errors.append(f"{workflow_id}: user intent must be required")
        if not contract.workflow_input.offline_input_ready:
            errors.append(f"{workflow_id}: input must be offline-ready")
        if not contract.plan.operator_editable:
            errors.append(f"{workflow_id}: plan must be operator-editable")
        if not contract.plan.approval_gate:
            errors.append(f"{workflow_id}: approval gate is required")
        if not contract.run.offline_ready:
            errors.append(f"{workflow_id}: run must be offline-ready")
        if not contract.run.controlled_tools:
            errors.append(f"{workflow_id}: controlled tools are required")
        if not contract.artifacts:
            errors.append(f"{workflow_id}: artifacts are required")
        if not contract.manifest.records_artifact_history:
            errors.append(f"{workflow_id}: manifest must record artifact history")
        if not contract.manifest.records_restore_metadata:
            errors.append(f"{workflow_id}: manifest must record restore metadata")
        if not contract.quality.must_fail_closed:
            errors.append(f"{workflow_id}: quality report must fail closed")
        if not contract.provenance.evidence_required:
            errors.append(f"{workflow_id}: provenance evidence is required")

        artifact_names = _artifact_names(contract)
        manifest_files = _manifest_files(contract)
        for required_manifest in DEFAULT_REQUIRED_MANIFESTS:
            if required_manifest not in manifest_files:
                errors.append(f"{workflow_id}: required manifest file missing from manifest: {required_manifest}")
        if "artifact_manifest.json" not in artifact_names:
            errors.append(f"{workflow_id}: artifact_manifest.json artifact is required")
        if "quality_report.json" not in artifact_names and contract.workflow_id != "slides":
            errors.append(f"{workflow_id}: quality_report.json artifact is required")
        if "source_evidence_manifest.json" not in artifact_names:
            errors.append(f"{workflow_id}: source_evidence_manifest.json artifact is required")
        for artifact in contract.artifacts:
            if artifact.required is not True:
                errors.append(f"{workflow_id}: artifact must be required: {artifact.name}")
            if artifact.provenance_required is not True:
                errors.append(f"{workflow_id}: artifact must require provenance: {artifact.name}")
            if not artifact.quality_gate:
                errors.append(f"{workflow_id}: artifact quality gate required: {artifact.name}")

    xlsx = WORKFLOW_CONTRACT_CORE.get("xlsx")
    if xlsx is not None:
        names = _artifact_names(xlsx)
        for required in ("workbook_manifest.json", "xlsx_analysis_report.json", "formula_inventory.json", "table_previews/*.csv"):
            if required not in names:
                errors.append(f"xlsx: {required} artifact is required")

    slides = WORKFLOW_CONTRACT_CORE.get("slides")
    if slides is not None:
        names = _artifact_names(slides)
        for required in ("deck.pptx", "independent_rendered_slides/*.png", "citation_manifest.json", "visual_qa_report.json"):
            if required not in names:
                errors.append(f"slides: {required} artifact is required")
        if slides.provenance.citation_manifest != "citation_manifest.json":
            errors.append("slides: citation_manifest.json provenance is required")

    browser = WORKFLOW_CONTRACT_CORE.get("browser_evidence")
    if browser is not None:
        if "approved" not in browser.run.browser_policy:
            errors.append("browser_evidence: browser policy must require approval")

    python_analysis = WORKFLOW_CONTRACT_CORE.get("python_analysis")
    if python_analysis is not None:
        names = _artifact_names(python_analysis)
        for required in ("analysis.py", "execution_log.txt", "analysis_results.json"):
            if required not in names:
                errors.append(f"python_analysis: {required} artifact is required")

    return errors
