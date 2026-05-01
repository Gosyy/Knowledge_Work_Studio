from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class WorkflowContract:
    workflow_id: str
    title: str
    user_visible: bool
    lifecycle: tuple[str, ...]
    input_kinds: tuple[str, ...]
    output_artifact_kinds: tuple[str, ...]
    required_events: tuple[str, ...]
    approval_gates: tuple[str, ...]
    provenance_required: bool
    offline_ready: bool
    browser_policy: str
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


REQUIRED_WORKFLOW_IDS = (
    "docx",
    "pdf",
    "slides",
    "data_python",
    "browser_assisted",
    "llm_provider",
)

_ALLOWED_BROWSER_POLICIES = {"none", "internal_only"}
_REQUIRED_EVENTS = (
    "workflow.plan.created",
    "workflow.execution.started",
    "workflow.execution.completed",
    "artifact.registered",
    "provenance.linked",
)

WORKFLOW_CONTRACTS: dict[str, WorkflowContract] = {
    "docx": WorkflowContract(
        workflow_id="docx",
        title="DOCX transform workflow",
        user_visible=True,
        lifecycle=(
            "intake",
            "source_validation",
            "plan_created",
            "user_review_optional",
            "document_transform",
            "artifact_generation",
            "artifact_history_registered",
        ),
        input_kinds=("docx", "instruction", "optional_reference_text"),
        output_artifact_kinds=("docx", "change_summary", "provenance_manifest"),
        required_events=_REQUIRED_EVENTS,
        approval_gates=("destructive_changes_require_explicit_confirmation",),
        provenance_required=True,
        offline_ready=True,
        browser_policy="none",
        notes=(
            "Preserve uploaded source identity and generated artifact history.",
            "Do not silently overwrite source files or historical versions.",
        ),
    ),
    "pdf": WorkflowContract(
        workflow_id="pdf",
        title="PDF understanding workflow",
        user_visible=True,
        lifecycle=(
            "intake",
            "source_validation",
            "text_or_page_extraction",
            "summary_or_analysis_plan",
            "artifact_generation",
            "artifact_history_registered",
        ),
        input_kinds=("pdf", "instruction", "optional_page_range"),
        output_artifact_kinds=("markdown", "pdf_summary", "provenance_manifest"),
        required_events=_REQUIRED_EVENTS,
        approval_gates=("operator_review_for_low_confidence_extraction",),
        provenance_required=True,
        offline_ready=True,
        browser_policy="none",
        notes=(
            "Prefer parsed text; OCR or visual extraction must be explicit and auditable.",
            "Summaries must preserve source/page references when available.",
        ),
    ),
    "slides": WorkflowContract(
        workflow_id="slides",
        title="Slides outline-first workflow",
        user_visible=True,
        lifecycle=(
            "intake",
            "outline_first_plan",
            "editable_plan_review",
            "template_or_adaptive_render_mode_selected",
            "artifact_generation",
            "artifact_history_registered",
            "plan_snapshot_registered",
        ),
        input_kinds=("instruction", "optional_source_files", "optional_template"),
        output_artifact_kinds=("pptx", "plan_snapshot", "diff", "provenance_manifest"),
        required_events=_REQUIRED_EVENTS + ("plan.snapshot.registered",),
        approval_gates=("editable_plan_before_generation", "retry_from_saved_plan"),
        provenance_required=True,
        offline_ready=True,
        browser_policy="none",
        notes=(
            "Kimi-derived product pattern: outline first, then editable plan, then generation.",
            "Template and adaptive modes are product modes; neither may bypass provenance.",
        ),
    ),
    "data_python": WorkflowContract(
        workflow_id="data_python",
        title="Spreadsheet and Python analysis workflow",
        user_visible=True,
        lifecycle=(
            "intake",
            "data_profile",
            "analysis_plan_created",
            "controlled_python_execution",
            "artifact_generation",
            "artifact_history_registered",
        ),
        input_kinds=("csv", "xlsx", "instruction", "optional_python_snippet"),
        output_artifact_kinds=("xlsx", "csv", "png_chart", "markdown_report", "provenance_manifest"),
        required_events=_REQUIRED_EVENTS + ("python.execution.recorded",),
        approval_gates=("operator_review_for_code_execution",),
        provenance_required=True,
        offline_ready=True,
        browser_policy="none",
        notes=(
            "Python execution must stay controlled, auditable, and artifact-oriented.",
            "Generated charts and tables must be downloadable artifacts, not only chat text.",
        ),
    ),
    "browser_assisted": WorkflowContract(
        workflow_id="browser_assisted",
        title="Browser-assisted internal workflow",
        user_visible=False,
        lifecycle=(
            "operator_requested_internal_browse_step",
            "approved_navigation_plan",
            "browser_runtime_execution",
            "captured_evidence_registered",
            "artifact_or_report_generation",
        ),
        input_kinds=("internal_url", "instruction", "optional_credentials_context"),
        output_artifact_kinds=("evidence_capture", "markdown_report", "provenance_manifest"),
        required_events=_REQUIRED_EVENTS + ("browser.step.recorded",),
        approval_gates=("explicit_internal_navigation_approval",),
        provenance_required=True,
        offline_ready=True,
        browser_policy="internal_only",
        notes=(
            "MVP browser runtime remains internal-only, not a full autonomous user-facing browser agent.",
            "No internet dependency is introduced by this contract.",
        ),
    ),
    "llm_provider": WorkflowContract(
        workflow_id="llm_provider",
        title="Offline LLM provider workflow",
        user_visible=False,
        lifecycle=(
            "provider_contract_loaded",
            "prompt_contract_built",
            "offline_provider_selected",
            "completion_recorded",
            "task_event_linked",
        ),
        input_kinds=("prompt_contract", "task_context", "source_manifest"),
        output_artifact_kinds=("completion_text", "provider_metadata", "provenance_manifest"),
        required_events=(
            "workflow.plan.created",
            "workflow.execution.started",
            "llm.provider.selected",
            "workflow.execution.completed",
            "provenance.linked",
        ),
        approval_gates=("offline_provider_must_be_gigachat_by_default",),
        provenance_required=True,
        offline_ready=True,
        browser_policy="none",
        notes=(
            "Default production provider is local GigaChat from S1.",
            "LiteLLM-compatible gateway is an optional transport, not a provider replacement.",
        ),
    ),
}


def list_workflow_contracts() -> tuple[WorkflowContract, ...]:
    return tuple(WORKFLOW_CONTRACTS[key] for key in REQUIRED_WORKFLOW_IDS)


def get_workflow_contract(workflow_id: str) -> WorkflowContract:
    return WORKFLOW_CONTRACTS[workflow_id]


def workflow_contract_report() -> dict[str, Any]:
    errors = validate_workflow_contracts()
    return {
        "status": "ready" if not errors else "not_ready",
        "required_workflow_ids": list(REQUIRED_WORKFLOW_IDS),
        "workflow_count": len(WORKFLOW_CONTRACTS),
        "contracts": {workflow_id: contract.as_dict() for workflow_id, contract in WORKFLOW_CONTRACTS.items()},
        "errors": errors,
    }


def validate_workflow_contracts() -> list[str]:
    errors: list[str] = []
    missing = [workflow_id for workflow_id in REQUIRED_WORKFLOW_IDS if workflow_id not in WORKFLOW_CONTRACTS]
    if missing:
        errors.append("missing workflow contract(s): " + ", ".join(missing))

    extra = sorted(set(WORKFLOW_CONTRACTS) - set(REQUIRED_WORKFLOW_IDS))
    if extra:
        errors.append("unexpected workflow contract(s): " + ", ".join(extra))

    for workflow_id, contract in WORKFLOW_CONTRACTS.items():
        if contract.workflow_id != workflow_id:
            errors.append(f"{workflow_id}: workflow_id field mismatch")
        if not contract.lifecycle:
            errors.append(f"{workflow_id}: lifecycle must not be empty")
        if not contract.required_events:
            errors.append(f"{workflow_id}: required_events must not be empty")
        if not contract.provenance_required:
            errors.append(f"{workflow_id}: provenance_required must be true")
        if not contract.offline_ready:
            errors.append(f"{workflow_id}: offline_ready must be true")
        if contract.browser_policy not in _ALLOWED_BROWSER_POLICIES:
            errors.append(f"{workflow_id}: browser_policy must be one of {sorted(_ALLOWED_BROWSER_POLICIES)}")

    slides = WORKFLOW_CONTRACTS.get("slides")
    if slides is not None:
        if "outline_first_plan" not in slides.lifecycle:
            errors.append("slides: outline_first_plan lifecycle stage is required")
        if "editable_plan_before_generation" not in slides.approval_gates:
            errors.append("slides: editable_plan_before_generation gate is required")
        if "plan_snapshot" not in slides.output_artifact_kinds:
            errors.append("slides: plan_snapshot output artifact is required")

    browser = WORKFLOW_CONTRACTS.get("browser_assisted")
    if browser is not None:
        if browser.user_visible:
            errors.append("browser_assisted: must remain internal-only and not user_visible")
        if browser.browser_policy != "internal_only":
            errors.append("browser_assisted: browser_policy must be internal_only")

    llm = WORKFLOW_CONTRACTS.get("llm_provider")
    if llm is not None:
        if "offline_provider_must_be_gigachat_by_default" not in llm.approval_gates:
            errors.append("llm_provider: GigaChat default approval gate is required")

    return errors
