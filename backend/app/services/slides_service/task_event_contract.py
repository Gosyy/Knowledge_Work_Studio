from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SLIDES_TASK_EVENT_STREAM_ID = "slides_plan_first_task_events"
SLIDES_TASK_WORKFLOW_ID = "slides"

EVENT_SCHEMA_REQUIRED_FIELDS = (
    "event_id",
    "task_id",
    "session_id",
    "workflow_id",
    "event_type",
    "created_at",
    "safe_payload",
)

SLIDES_TASK_EVENT_TYPES = (
    "slides.task.created",
    "slides.plan.requested",
    "slides.outline.created",
    "slides.plan.ready_for_review",
    "slides.plan.approved",
    "slides.render_mode.selected",
    "slides.generation.started",
    "artifact.registered",
    "plan.snapshot.registered",
    "slides.generation.completed",
    "slides.retry.from_saved_plan.requested",
    "slides.retry.saved_plan_snapshot.loaded",
    "slides.retry.plan.validated",
    "slides.retry.render_mode.confirmed",
    "slides.retry.generation.started",
    "slides.retry.generation.completed",
    "slides.task.failed",
)

SLIDES_RETRY_EVENT_SEQUENCE = (
    "slides.retry.from_saved_plan.requested",
    "slides.retry.saved_plan_snapshot.loaded",
    "slides.retry.plan.validated",
    "slides.retry.render_mode.confirmed",
    "slides.retry.generation.started",
    "artifact.registered",
    "plan.snapshot.registered",
    "slides.retry.generation.completed",
)

SLIDES_PLAN_FIRST_ORDER_CONSTRAINTS = (
    ("slides.plan.requested", "slides.outline.created"),
    ("slides.outline.created", "slides.plan.ready_for_review"),
    ("slides.plan.ready_for_review", "slides.plan.approved"),
    ("slides.plan.approved", "slides.render_mode.selected"),
    ("slides.render_mode.selected", "slides.generation.started"),
    ("slides.generation.started", "artifact.registered"),
    ("artifact.registered", "plan.snapshot.registered"),
    ("plan.snapshot.registered", "slides.generation.completed"),
)

SLIDES_RETRY_ORDER_CONSTRAINTS = (
    ("slides.retry.from_saved_plan.requested", "slides.retry.saved_plan_snapshot.loaded"),
    ("slides.retry.saved_plan_snapshot.loaded", "slides.retry.plan.validated"),
    ("slides.retry.plan.validated", "slides.retry.render_mode.confirmed"),
    ("slides.retry.render_mode.confirmed", "slides.retry.generation.started"),
    ("slides.retry.generation.started", "artifact.registered"),
    ("artifact.registered", "plan.snapshot.registered"),
    ("plan.snapshot.registered", "slides.retry.generation.completed"),
)

SAFE_PAYLOAD_FIELDS = (
    "plan_snapshot_id",
    "presentation_id",
    "presentation_version_id",
    "render_mode",
    "artifact_id",
    "artifact_filename",
    "retry_of_task_id",
    "change_summary",
    "error_code",
)

REDACTED_PAYLOAD_KEYS = (
    "password",
    "secret",
    "token",
    "api_key",
    "client_secret",
    "database_url",
    "authorization",
)

RETRY_REQUIRED_CONTEXT_FIELDS = (
    "saved_plan_snapshot_id",
    "source_presentation_id",
    "source_presentation_version_id",
    "operator_instruction",
    "render_mode",
)


@dataclass(frozen=True)
class SlidesTaskEventStreamContract:
    stream_id: str
    workflow_id: str
    title: str
    event_schema_required_fields: tuple[str, ...]
    event_types: tuple[str, ...]
    plan_first_order_constraints: tuple[tuple[str, str], ...]
    retry_event_sequence: tuple[str, ...]
    retry_order_constraints: tuple[tuple[str, str], ...]
    retry_required_context_fields: tuple[str, ...]
    safe_payload_fields: tuple[str, ...]
    redacted_payload_keys: tuple[str, ...]
    terminal_event_types: tuple[str, ...]
    failure_event_types: tuple[str, ...]
    append_only_stream: bool
    retry_requires_saved_plan_snapshot: bool
    retry_requires_explicit_operator_instruction: bool
    retry_requires_render_mode_confirmation: bool
    retry_links_parent_plan_snapshot: bool
    retry_must_register_new_artifact: bool
    offline_ready: bool
    provenance_required: bool
    browser_policy: str
    non_goals: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


SLIDES_TASK_EVENT_STREAM_CONTRACT = SlidesTaskEventStreamContract(
    stream_id=SLIDES_TASK_EVENT_STREAM_ID,
    workflow_id=SLIDES_TASK_WORKFLOW_ID,
    title="Slides task event stream and saved-plan retry contract",
    event_schema_required_fields=EVENT_SCHEMA_REQUIRED_FIELDS,
    event_types=SLIDES_TASK_EVENT_TYPES,
    plan_first_order_constraints=SLIDES_PLAN_FIRST_ORDER_CONSTRAINTS,
    retry_event_sequence=SLIDES_RETRY_EVENT_SEQUENCE,
    retry_order_constraints=SLIDES_RETRY_ORDER_CONSTRAINTS,
    retry_required_context_fields=RETRY_REQUIRED_CONTEXT_FIELDS,
    safe_payload_fields=SAFE_PAYLOAD_FIELDS,
    redacted_payload_keys=REDACTED_PAYLOAD_KEYS,
    terminal_event_types=("slides.generation.completed", "slides.retry.generation.completed"),
    failure_event_types=("slides.task.failed",),
    append_only_stream=True,
    retry_requires_saved_plan_snapshot=True,
    retry_requires_explicit_operator_instruction=True,
    retry_requires_render_mode_confirmation=True,
    retry_links_parent_plan_snapshot=True,
    retry_must_register_new_artifact=True,
    offline_ready=True,
    provenance_required=True,
    browser_policy="none",
    non_goals=(
        "No new async worker runtime in S4.",
        "No queue broker or event store migration in S4.",
        "No PPTX renderer rewrite in S4.",
        "No browser or internet dependency in S4.",
    ),
)


def _missing(items: tuple[str, ...], required: tuple[str, ...]) -> list[str]:
    return [item for item in required if item not in items]


def _validate_order(
    constraints: tuple[tuple[str, str], ...],
    available_sequence: tuple[str, ...],
    label: str,
) -> list[str]:
    errors: list[str] = []
    for before, after in constraints:
        try:
            before_index = available_sequence.index(before)
            after_index = available_sequence.index(after)
        except ValueError as exc:
            errors.append(f"{label} order references missing event: {exc}")
            continue
        if before_index >= after_index:
            errors.append(f"{label} order violation: {before} must precede {after}")
    return errors


def validate_slides_task_event_stream_contract(
    contract: SlidesTaskEventStreamContract = SLIDES_TASK_EVENT_STREAM_CONTRACT,
) -> list[str]:
    errors: list[str] = []

    if contract.stream_id != SLIDES_TASK_EVENT_STREAM_ID:
        errors.append("stream_id must be slides_plan_first_task_events")
    if contract.workflow_id != "slides":
        errors.append("workflow_id must be slides")
    if not contract.append_only_stream:
        errors.append("task event stream must be append-only")
    if not contract.offline_ready:
        errors.append("offline_ready must be true")
    if not contract.provenance_required:
        errors.append("provenance_required must be true")
    if contract.browser_policy != "none":
        errors.append("slides task events must not require browser runtime")

    required_schema = (
        "event_id",
        "task_id",
        "session_id",
        "workflow_id",
        "event_type",
        "created_at",
        "safe_payload",
    )
    for field in _missing(contract.event_schema_required_fields, required_schema):
        errors.append(f"missing event schema field: {field}")

    critical_events = (
        "slides.plan.requested",
        "slides.plan.ready_for_review",
        "slides.plan.approved",
        "slides.render_mode.selected",
        "slides.generation.started",
        "artifact.registered",
        "plan.snapshot.registered",
        "slides.generation.completed",
        "slides.retry.from_saved_plan.requested",
        "slides.retry.saved_plan_snapshot.loaded",
        "slides.retry.plan.validated",
        "slides.retry.render_mode.confirmed",
        "slides.retry.generation.started",
        "slides.retry.generation.completed",
        "slides.task.failed",
    )
    for event_type in _missing(contract.event_types, critical_events):
        errors.append(f"missing event type: {event_type}")

    for context_field in _missing(contract.retry_required_context_fields, RETRY_REQUIRED_CONTEXT_FIELDS):
        errors.append(f"missing retry context field: {context_field}")

    if not contract.retry_requires_saved_plan_snapshot:
        errors.append("retry_requires_saved_plan_snapshot must be true")
    if not contract.retry_requires_explicit_operator_instruction:
        errors.append("retry_requires_explicit_operator_instruction must be true")
    if not contract.retry_requires_render_mode_confirmation:
        errors.append("retry_requires_render_mode_confirmation must be true")
    if not contract.retry_links_parent_plan_snapshot:
        errors.append("retry_links_parent_plan_snapshot must be true")
    if not contract.retry_must_register_new_artifact:
        errors.append("retry_must_register_new_artifact must be true")

    for key in ("secret", "token", "api_key", "client_secret", "database_url"):
        if key not in contract.redacted_payload_keys:
            errors.append(f"missing redacted payload key: {key}")

    errors.extend(_validate_order(contract.plan_first_order_constraints, contract.event_types, "plan-first"))
    errors.extend(_validate_order(contract.retry_order_constraints, contract.retry_event_sequence, "retry"))

    return errors


def slides_task_event_stream_report(
    *,
    mode: str | None = None,
    contract: SlidesTaskEventStreamContract = SLIDES_TASK_EVENT_STREAM_CONTRACT,
) -> dict[str, Any]:
    errors = validate_slides_task_event_stream_contract(contract)
    selected_mode = mode or "all"

    if mode is not None and mode not in {"stream", "retry"}:
        errors.append(f"unknown mode: {mode}")

    if mode == "retry":
        selected_events = contract.retry_event_sequence
        selected_constraints = contract.retry_order_constraints
    elif mode == "stream":
        selected_events = contract.event_types
        selected_constraints = contract.plan_first_order_constraints
    else:
        selected_events = contract.event_types
        selected_constraints = contract.plan_first_order_constraints + contract.retry_order_constraints

    controls = {
        "append_only_stream": contract.append_only_stream,
        "safe_payload_only": True,
        "redaction_required": True,
        "retry_requires_saved_plan_snapshot": contract.retry_requires_saved_plan_snapshot,
        "retry_requires_explicit_operator_instruction": contract.retry_requires_explicit_operator_instruction,
        "retry_requires_render_mode_confirmation": contract.retry_requires_render_mode_confirmation,
        "retry_links_parent_plan_snapshot": contract.retry_links_parent_plan_snapshot,
        "retry_must_register_new_artifact": contract.retry_must_register_new_artifact,
    }

    return {
        "status": "ready" if not errors else "not_ready",
        "stream_id": contract.stream_id,
        "workflow_id": contract.workflow_id,
        "selected_mode": selected_mode,
        "selected_events": selected_events,
        "selected_order_constraints": selected_constraints,
        "controls": controls,
        "contract": contract.as_dict(),
        "errors": errors,
    }
