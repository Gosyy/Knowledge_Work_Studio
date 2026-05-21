from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.runtime_closure import (
    RF2_SLIDES_RUNTIME_CAPABILITIES,
    RF2_SLIDES_RUNTIME_CHECKPOINTS,
    build_slides_runtime_closure_readiness,
    validate_slides_runtime_closure_readiness,
)

RF2_FINAL_CLOSURE_CHECKPOINT = "RF2_closure"
RF2_FINAL_CLOSED_CHECKPOINTS: tuple[str, ...] = (
    *RF2_SLIDES_RUNTIME_CHECKPOINTS,
    "RF2.7",
)
RF2_FINAL_NEXT_ROUTE: tuple[str, ...] = (
    "RF3",
    "RF4",
    "RF_closure",
    "K0",
)
RF2_FINAL_REQUIRED_CHECKERS: tuple[str, ...] = (
    "scripts/kw_slides_runtime_phase_check.py",
    "scripts/kw_slides_runtime_inventory_check.py",
    "scripts/kw_slides_approved_plan_runtime_check.py",
    "scripts/kw_rf_to_k_transition_check.py",
    "scripts/kw_slides_approved_plan_lifecycle_check.py",
    "scripts/kw_slides_saved_plan_retry_check.py",
    "scripts/kw_slides_render_mode_runtime_check.py",
    "scripts/kw_slides_provenance_manifest_runtime_check.py",
    "scripts/kw_slides_runtime_closure_check.py",
)
RF2_FINAL_REQUIRED_DOCS: tuple[str, ...] = (
    "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md",
    "docs/codex/SLIDES_RUNTIME_CAPABILITY_INVENTORY.md",
    "docs/codex/SLIDES_APPROVED_PLAN_RUNTIME.md",
    "docs/codex/SLIDES_APPROVED_PLAN_LIFECYCLE_RUNTIME.md",
    "docs/codex/SLIDES_SAVED_PLAN_RETRY_RUNTIME.md",
    "docs/codex/SLIDES_RENDER_MODE_RUNTIME_HARDENING.md",
    "docs/codex/SLIDES_PROVENANCE_MANIFEST_RUNTIME.md",
    "docs/codex/SLIDES_RUNTIME_RF2_CLOSURE.md",
    "docs/codex/SLIDES_RUNTIME_RF2_FINAL_CLOSURE.md",
)
RF2_FINAL_NON_GOALS: tuple[str, ...] = (
    "no_public_api_endpoint_added_by_rf2_closure",
    "no_db_schema_migration_added_by_rf2_closure",
    "no_queue_or_event_store_migration_added_by_rf2_closure",
    "no_visual_qa_runtime_added_by_rf2_closure",
    "no_k_phase_work_started_by_rf2_closure",
    "no_kimi_level_claim_by_rf2_closure",
    "no_dependency_version_changes_by_rf2_closure",
    "no_dockerfile_changes_by_rf2_closure",
    "no_npm_audit_fix_force_by_rf2_closure",
)


@dataclass(frozen=True)
class RF2FinalClosureReport:
    checkpoint: str
    closed_checkpoints: tuple[str, ...]
    capabilities: tuple[str, ...]
    required_checkers: tuple[str, ...]
    required_docs: tuple[str, ...]
    non_goals_preserved: tuple[str, ...]
    next_route: tuple[str, ...]
    rf2_slides_runtime_foundation_closed: bool
    rf2_slides_path_ready_for_rf3: bool
    rf2_closure_is_feature_free_checkpoint: bool
    rf3_ready_to_start: bool
    rf4_ready_after_rf3: bool
    k_phase_started_by_rf2_closure: bool
    k_phase_ready_to_start: bool
    kimi_grade_supported: bool
    whole_project_kimi_level_supported: bool
    runtime_changed_by_rf2_closure: bool
    dependency_versions_changed_by_rf2_closure: bool
    dockerfiles_changed_by_rf2_closure: bool
    api_endpoint_added_by_rf2_closure: bool
    db_schema_migration_added_by_rf2_closure: bool
    queue_or_event_store_migration_added_by_rf2_closure: bool
    visual_qa_runtime_added_by_rf2_closure: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_rf2_final_closure_report() -> RF2FinalClosureReport:
    """Return the final RF2 closure checkpoint report.

    RF2_closure closes the RF2 slides runtime foundation. It intentionally does
    not add a new runtime feature or start K-phase product-power work.
    """

    rf2_7_readiness = build_slides_runtime_closure_readiness()
    return RF2FinalClosureReport(
        checkpoint=RF2_FINAL_CLOSURE_CHECKPOINT,
        closed_checkpoints=RF2_FINAL_CLOSED_CHECKPOINTS,
        capabilities=RF2_SLIDES_RUNTIME_CAPABILITIES,
        required_checkers=RF2_FINAL_REQUIRED_CHECKERS,
        required_docs=RF2_FINAL_REQUIRED_DOCS,
        non_goals_preserved=RF2_FINAL_NON_GOALS,
        next_route=RF2_FINAL_NEXT_ROUTE,
        rf2_slides_runtime_foundation_closed=True,
        rf2_slides_path_ready_for_rf3=rf2_7_readiness.rf2_slides_path_ready_for_closure,
        rf2_closure_is_feature_free_checkpoint=True,
        rf3_ready_to_start=True,
        rf4_ready_after_rf3=True,
        k_phase_started_by_rf2_closure=False,
        k_phase_ready_to_start=False,
        kimi_grade_supported=False,
        whole_project_kimi_level_supported=False,
        runtime_changed_by_rf2_closure=False,
        dependency_versions_changed_by_rf2_closure=False,
        dockerfiles_changed_by_rf2_closure=False,
        api_endpoint_added_by_rf2_closure=False,
        db_schema_migration_added_by_rf2_closure=False,
        queue_or_event_store_migration_added_by_rf2_closure=False,
        visual_qa_runtime_added_by_rf2_closure=False,
    )


def validate_rf2_final_closure_report(
    report: RF2FinalClosureReport | None = None,
) -> list[str]:
    item = report or build_rf2_final_closure_report()
    errors: list[str] = []

    rf2_7_errors = validate_slides_runtime_closure_readiness()
    errors.extend(f"RF2.7 readiness: {error}" for error in rf2_7_errors)

    if item.checkpoint != RF2_FINAL_CLOSURE_CHECKPOINT:
        errors.append("checkpoint must be RF2_closure")

    for checkpoint in RF2_FINAL_CLOSED_CHECKPOINTS:
        if checkpoint not in item.closed_checkpoints:
            errors.append(f"missing closed checkpoint: {checkpoint}")

    for capability in RF2_SLIDES_RUNTIME_CAPABILITIES:
        if capability not in item.capabilities:
            errors.append(f"missing RF2 capability: {capability}")

    for checker in RF2_FINAL_REQUIRED_CHECKERS:
        if checker not in item.required_checkers:
            errors.append(f"missing required RF2 checker: {checker}")

    for doc in RF2_FINAL_REQUIRED_DOCS:
        if doc not in item.required_docs:
            errors.append(f"missing required RF2 doc: {doc}")

    expected_route = RF2_FINAL_NEXT_ROUTE
    if tuple(item.next_route) != expected_route:
        errors.append("RF2_closure next route must be RF3 -> RF4 -> RF_closure -> K0")

    true_flags = (
        "rf2_slides_runtime_foundation_closed",
        "rf2_slides_path_ready_for_rf3",
        "rf2_closure_is_feature_free_checkpoint",
        "rf3_ready_to_start",
        "rf4_ready_after_rf3",
    )
    for flag in true_flags:
        if not bool(getattr(item, flag)):
            errors.append(f"{flag} must be true")

    false_flags = (
        "k_phase_started_by_rf2_closure",
        "k_phase_ready_to_start",
        "kimi_grade_supported",
        "whole_project_kimi_level_supported",
        "runtime_changed_by_rf2_closure",
        "dependency_versions_changed_by_rf2_closure",
        "dockerfiles_changed_by_rf2_closure",
        "api_endpoint_added_by_rf2_closure",
        "db_schema_migration_added_by_rf2_closure",
        "queue_or_event_store_migration_added_by_rf2_closure",
        "visual_qa_runtime_added_by_rf2_closure",
    )
    for flag in false_flags:
        if bool(getattr(item, flag)):
            errors.append(f"{flag} must be false")

    for non_goal in RF2_FINAL_NON_GOALS:
        if non_goal not in item.non_goals_preserved:
            errors.append(f"missing RF2_closure non-goal: {non_goal}")

    return errors
