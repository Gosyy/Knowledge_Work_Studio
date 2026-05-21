from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SLIDES_RENDER_MODE_WORKFLOW_ID = "slides.render_modes"
ADAPTIVE_RENDER_MODE = "adaptive"
TEMPLATE_RENDER_MODE = "template"
RENDER_MODES = (ADAPTIVE_RENDER_MODE, TEMPLATE_RENDER_MODE)

RENDER_MODE_EVENTS = (
    "slides.plan.approved",
    "slides.render_mode.selected",
    "slides.render_mode.validated",
    "slides.render_mode.applied",
    "slides.generation.started",
    "artifact.registered",
    "plan.snapshot.registered",
    "slides.generation.completed",
)

RENDER_MODE_NON_GOALS = (
    "No PPTX renderer rewrite in S6.",
    "No full slide editor in S6.",
    "No new async runtime in S6.",
    "No browser or internet dependency in S6.",
)


@dataclass(frozen=True)
class SlidesRenderModePolicy:
    mode: str
    title: str
    layout_policy: str
    requires_approved_plan: bool
    requires_plan_snapshot: bool
    requires_render_mode_event: bool
    template_id_required: bool
    template_locked: bool
    allows_adaptive_layout_selection: bool
    allows_external_template_download: bool
    artifact_metadata_required: tuple[str, ...]
    safe_task_events: tuple[str, ...]
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


ADAPTIVE_RENDER_POLICY = SlidesRenderModePolicy(
    mode=ADAPTIVE_RENDER_MODE,
    title="Adaptive render mode",
    layout_policy="select_layouts_from_approved_plan_and_local_template_library",
    requires_approved_plan=True,
    requires_plan_snapshot=True,
    requires_render_mode_event=True,
    template_id_required=False,
    template_locked=False,
    allows_adaptive_layout_selection=True,
    allows_external_template_download=False,
    artifact_metadata_required=(
        "render_mode",
        "plan_snapshot_id",
        "layout_policy",
        "template_source",
    ),
    safe_task_events=RENDER_MODE_EVENTS,
    notes=(
        "Adaptive mode may choose local layouts from the approved plan and bundled templates.",
        "Adaptive mode must not fetch templates from the internet.",
    ),
)

TEMPLATE_RENDER_POLICY = SlidesRenderModePolicy(
    mode=TEMPLATE_RENDER_MODE,
    title="Template render mode",
    layout_policy="render_with_operator_selected_local_template_id",
    requires_approved_plan=True,
    requires_plan_snapshot=True,
    requires_render_mode_event=True,
    template_id_required=True,
    template_locked=True,
    allows_adaptive_layout_selection=False,
    allows_external_template_download=False,
    artifact_metadata_required=(
        "render_mode",
        "plan_snapshot_id",
        "layout_policy",
        "template_id",
        "template_source",
    ),
    safe_task_events=RENDER_MODE_EVENTS,
    notes=(
        "Template mode must use an explicit local template identifier.",
        "Template mode must not silently fall back to adaptive layout selection.",
    ),
)

RENDER_MODE_POLICIES = {
    ADAPTIVE_RENDER_MODE: ADAPTIVE_RENDER_POLICY,
    TEMPLATE_RENDER_MODE: TEMPLATE_RENDER_POLICY,
}


@dataclass(frozen=True)
class SlidesRenderModeContract:
    workflow_id: str
    title: str
    offline_ready: bool
    provenance_required: bool
    browser_policy: str
    default_mode: str
    allowed_modes: tuple[str, ...]
    policies: tuple[SlidesRenderModePolicy, ...]
    non_goals: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "title": self.title,
            "offline_ready": self.offline_ready,
            "provenance_required": self.provenance_required,
            "browser_policy": self.browser_policy,
            "default_mode": self.default_mode,
            "allowed_modes": list(self.allowed_modes),
            "policies": {policy.mode: policy.as_dict() for policy in self.policies},
            "non_goals": list(self.non_goals),
        }


SLIDES_RENDER_MODE_CONTRACT = SlidesRenderModeContract(
    workflow_id=SLIDES_RENDER_MODE_WORKFLOW_ID,
    title="Slides adaptive/template render mode contract",
    offline_ready=True,
    provenance_required=True,
    browser_policy="none",
    default_mode=ADAPTIVE_RENDER_MODE,
    allowed_modes=RENDER_MODES,
    policies=(ADAPTIVE_RENDER_POLICY, TEMPLATE_RENDER_POLICY),
    non_goals=RENDER_MODE_NON_GOALS,
)


def validate_render_mode_policy(policy: SlidesRenderModePolicy) -> list[str]:
    errors: list[str] = []
    if policy.mode not in RENDER_MODES:
        errors.append(f"unknown render mode policy: {policy.mode}")
    if not policy.requires_approved_plan:
        errors.append(f"{policy.mode}: approved plan is required")
    if not policy.requires_plan_snapshot:
        errors.append(f"{policy.mode}: plan snapshot is required")
    if not policy.requires_render_mode_event:
        errors.append(f"{policy.mode}: render mode event is required")
    if policy.allows_external_template_download:
        errors.append(f"{policy.mode}: external template download must not be allowed")
    for event in RENDER_MODE_EVENTS:
        if event not in policy.safe_task_events:
            errors.append(f"{policy.mode}: missing safe task event {event}")
    for field in ("render_mode", "plan_snapshot_id", "layout_policy", "template_source"):
        if field not in policy.artifact_metadata_required:
            errors.append(f"{policy.mode}: missing artifact metadata field {field}")
    if policy.mode == TEMPLATE_RENDER_MODE:
        if not policy.template_id_required:
            errors.append("template mode must require template_id")
        if not policy.template_locked:
            errors.append("template mode must be template_locked")
        if policy.allows_adaptive_layout_selection:
            errors.append("template mode must not allow adaptive layout selection")
        if "template_id" not in policy.artifact_metadata_required:
            errors.append("template mode must register template_id metadata")
    if policy.mode == ADAPTIVE_RENDER_MODE:
        if policy.template_id_required:
            errors.append("adaptive mode must not require template_id")
        if policy.template_locked:
            errors.append("adaptive mode must not be template_locked")
        if not policy.allows_adaptive_layout_selection:
            errors.append("adaptive mode must allow adaptive layout selection")
    return errors


def validate_slides_render_mode_contract(
    contract: SlidesRenderModeContract = SLIDES_RENDER_MODE_CONTRACT,
) -> list[str]:
    errors: list[str] = []
    if contract.workflow_id != SLIDES_RENDER_MODE_WORKFLOW_ID:
        errors.append("workflow_id must be slides.render_modes")
    if not contract.offline_ready:
        errors.append("offline_ready must be true")
    if not contract.provenance_required:
        errors.append("provenance_required must be true")
    if contract.browser_policy != "none":
        errors.append("slides render modes must not require browser runtime")
    if contract.default_mode != ADAPTIVE_RENDER_MODE:
        errors.append("default render mode must be adaptive")
    for mode in RENDER_MODES:
        if mode not in contract.allowed_modes:
            errors.append(f"missing allowed render mode: {mode}")
    seen_modes = {policy.mode for policy in contract.policies}
    for mode in RENDER_MODES:
        if mode not in seen_modes:
            errors.append(f"missing render mode policy: {mode}")
    for policy in contract.policies:
        errors.extend(validate_render_mode_policy(policy))
    return errors


def validate_render_request(
    *,
    mode: str,
    plan_snapshot_id: str | None,
    approved_plan: bool,
    template_id: str | None = None,
) -> list[str]:
    errors: list[str] = []
    policy = RENDER_MODE_POLICIES.get(mode)
    if policy is None:
        return [f"unknown render mode: {mode}"]
    if policy.requires_approved_plan and not approved_plan:
        errors.append("approved plan is required before rendering")
    if policy.requires_plan_snapshot and not (plan_snapshot_id or "").strip():
        errors.append("plan_snapshot_id is required before rendering")
    if policy.template_id_required and not (template_id or "").strip():
        errors.append("template_id is required for template render mode")
    if not policy.template_id_required and template_id:
        errors.append("template_id must not be required by adaptive render mode")
    return errors


def slides_render_mode_report(
    *,
    mode: str | None = None,
    template_id: str | None = None,
    plan_snapshot_id: str | None = "plansnap_contract",
    approved_plan: bool = True,
    contract: SlidesRenderModeContract = SLIDES_RENDER_MODE_CONTRACT,
) -> dict[str, Any]:
    errors = validate_slides_render_mode_contract(contract)
    selected_mode = mode or contract.default_mode
    if selected_mode not in RENDER_MODE_POLICIES:
        errors.append(f"unknown render mode: {selected_mode}")
        policy_payload: dict[str, Any] = {}
        request_errors: list[str] = []
    else:
        policy = RENDER_MODE_POLICIES[selected_mode]
        policy_payload = policy.as_dict()
        request_errors = validate_render_request(
            mode=selected_mode,
            plan_snapshot_id=plan_snapshot_id,
            approved_plan=approved_plan,
            template_id=template_id,
        )
        errors.extend(request_errors)
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": contract.workflow_id,
        "selected_mode": selected_mode,
        "default_mode": contract.default_mode,
        "allowed_modes": list(contract.allowed_modes),
        "policy": policy_payload,
        "request": {
            "approved_plan": approved_plan,
            "plan_snapshot_id_configured": bool((plan_snapshot_id or "").strip()),
            "template_id_configured": bool((template_id or "").strip()),
        },
        "contract": contract.as_dict(),
        "errors": errors,
    }
