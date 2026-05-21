from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SLIDES_PLAN_FIRST_WORKFLOW_ID = "slides"

PLAN_FIRST_STAGES = (
    "source_intake",
    "outline_draft",
    "editable_plan_review",
    "render_mode_selection",
    "approved_plan_generation",
    "artifact_history_registration",
    "plan_snapshot_registration",
    "retry_from_saved_plan",
)

RENDER_MODES = ("adaptive", "template")

SAFE_TASK_EVENTS = (
    "slides.plan.requested",
    "slides.outline.created",
    "slides.plan.ready_for_review",
    "slides.plan.approved",
    "slides.render_mode.selected",
    "slides.generation.started",
    "artifact.registered",
    "plan.snapshot.registered",
    "slides.retry.from_saved_plan.requested",
    "slides.generation.completed",
)

REQUIRED_APPROVAL_GATES = (
    "editable_plan_before_generation",
    "explicit_render_mode_selection",
    "retry_from_saved_plan",
)

KIMI_DERIVED_PATTERNS = (
    "outline_first",
    "editable_plan_before_generation",
    "adaptive_or_template_render_mode",
    "retry_from_saved_plan",
    "visible_task_event_stream",
)


@dataclass(frozen=True)
class SlidesPlanFirstUxContract:
    workflow_id: str
    title: str
    user_goal: str
    stages: tuple[str, ...]
    render_modes: tuple[str, ...]
    approval_gates: tuple[str, ...]
    safe_task_events: tuple[str, ...]
    kimi_derived_patterns: tuple[str, ...]
    generation_requires_approved_plan: bool
    retry_from_saved_plan_required: bool
    explicit_render_mode_required: bool
    direct_generate_without_plan_allowed: bool
    offline_ready: bool
    provenance_required: bool
    browser_policy: str
    non_goals: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


SLIDES_PLAN_FIRST_UX_CONTRACT = SlidesPlanFirstUxContract(
    workflow_id=SLIDES_PLAN_FIRST_WORKFLOW_ID,
    title="Slides plan-first UX contract",
    user_goal=(
        "Create or revise decks through an editable outline/plan before generation, "
        "then regenerate safely from a saved plan with a visible event trail."
    ),
    stages=PLAN_FIRST_STAGES,
    render_modes=RENDER_MODES,
    approval_gates=REQUIRED_APPROVAL_GATES,
    safe_task_events=SAFE_TASK_EVENTS,
    kimi_derived_patterns=KIMI_DERIVED_PATTERNS,
    generation_requires_approved_plan=True,
    retry_from_saved_plan_required=True,
    explicit_render_mode_required=True,
    direct_generate_without_plan_allowed=False,
    offline_ready=True,
    provenance_required=True,
    browser_policy="none",
    non_goals=(
        "No full slide editor in S3.",
        "No new PPTX renderer in S3.",
        "No autonomous browser workflow in S3.",
        "No internet dependency in S3.",
    ),
)


def _index_of(items: tuple[str, ...], value: str) -> int:
    try:
        return items.index(value)
    except ValueError:
        return -1


def validate_slides_plan_first_contract(
    contract: SlidesPlanFirstUxContract = SLIDES_PLAN_FIRST_UX_CONTRACT,
) -> list[str]:
    errors: list[str] = []

    if contract.workflow_id != "slides":
        errors.append("workflow_id must be slides")
    if not contract.offline_ready:
        errors.append("offline_ready must be true")
    if not contract.provenance_required:
        errors.append("provenance_required must be true")
    if contract.browser_policy != "none":
        errors.append("slides plan-first UX must not require browser runtime")
    if contract.direct_generate_without_plan_allowed:
        errors.append("direct generation without an approved plan must not be allowed")
    if not contract.generation_requires_approved_plan:
        errors.append("generation_requires_approved_plan must be true")
    if not contract.retry_from_saved_plan_required:
        errors.append("retry_from_saved_plan_required must be true")
    if not contract.explicit_render_mode_required:
        errors.append("explicit_render_mode_required must be true")

    for mode in ("adaptive", "template"):
        if mode not in contract.render_modes:
            errors.append(f"missing render mode: {mode}")

    for gate in REQUIRED_APPROVAL_GATES:
        if gate not in contract.approval_gates:
            errors.append(f"missing approval gate: {gate}")

    for event in SAFE_TASK_EVENTS:
        if event not in contract.safe_task_events:
            errors.append(f"missing task event: {event}")

    required_stage_order = (
        "outline_draft",
        "editable_plan_review",
        "render_mode_selection",
        "approved_plan_generation",
        "artifact_history_registration",
        "plan_snapshot_registration",
        "retry_from_saved_plan",
    )
    previous = -1
    for stage in required_stage_order:
        current = _index_of(contract.stages, stage)
        if current < 0:
            errors.append(f"missing stage: {stage}")
            continue
        if current <= previous:
            errors.append(f"stage order violation near: {stage}")
        previous = current

    for pattern in KIMI_DERIVED_PATTERNS:
        if pattern not in contract.kimi_derived_patterns:
            errors.append(f"missing Kimi-derived pattern: {pattern}")

    return errors


def slides_plan_first_report(
    *,
    mode: str | None = None,
    contract: SlidesPlanFirstUxContract = SLIDES_PLAN_FIRST_UX_CONTRACT,
) -> dict[str, Any]:
    errors = validate_slides_plan_first_contract(contract)
    selected_mode = mode or "all"
    if mode is not None and mode not in contract.render_modes:
        errors.append(f"unknown render mode: {mode}")

    controls = {
        "plan_review_required": contract.generation_requires_approved_plan,
        "retry_from_saved_plan_required": contract.retry_from_saved_plan_required,
        "explicit_render_mode_required": contract.explicit_render_mode_required,
        "direct_generate_without_plan_allowed": contract.direct_generate_without_plan_allowed,
    }

    if mode == "adaptive":
        controls["template_required"] = False
        controls["layout_policy"] = "adaptive_layout_from_approved_plan"
    elif mode == "template":
        controls["template_required"] = True
        controls["layout_policy"] = "template_constrained_layout_from_approved_plan"
    else:
        controls["template_required"] = "mode_dependent"
        controls["layout_policy"] = "adaptive_or_template_from_approved_plan"

    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": contract.workflow_id,
        "selected_mode": selected_mode,
        "contract": contract.as_dict(),
        "controls": controls,
        "errors": errors,
    }
