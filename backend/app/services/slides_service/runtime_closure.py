from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

RF2_SLIDES_RUNTIME_CHECKPOINTS: tuple[str, ...] = (
    "RF2.0",
    "RF2.1",
    "RF2.2",
    "RF2.2a",
    "RF2.3",
    "RF2.4",
    "RF2.5",
    "RF2.6",
)

RF2_SLIDES_RUNTIME_CAPABILITIES: tuple[str, ...] = (
    "slides_runtime_phase_checkpoint",
    "slides_runtime_inventory_and_baseline_smoke",
    "approved_plan_deterministic_pptx_runtime",
    "rf_to_k_transition_guard",
    "approved_plan_snapshot_artifact_event_lifecycle",
    "saved_plan_retry_runtime_path",
    "adaptive_template_local_render_mode_hardening",
    "downloadable_provenance_manifest_runtime_link",
)

RF2_SLIDES_RUNTIME_NON_GOALS: tuple[str, ...] = (
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

RF2_SLIDES_RUNTIME_NEXT_ROUTE: tuple[str, ...] = (
    "RF2_closure",
    "RF3",
    "RF4",
    "RF_closure",
    "K0",
)


@dataclass(frozen=True)
class SlidesRuntimeClosureReadiness:
    checkpoint: str
    closed_checkpoints: tuple[str, ...]
    capabilities: tuple[str, ...]
    non_goals_preserved: tuple[str, ...]
    next_route: tuple[str, ...]
    approved_plan_runtime_ready: bool
    lifecycle_runtime_ready: bool
    saved_plan_retry_ready: bool
    render_mode_runtime_ready: bool
    provenance_manifest_runtime_ready: bool
    rf2_slides_path_ready_for_closure: bool
    k_phase_ready_to_start: bool
    kimi_grade_supported: bool
    whole_project_kimi_level_supported: bool
    dependency_versions_changed_by_rf2_7: bool
    dockerfiles_changed_by_rf2_7: bool
    api_endpoint_added_by_rf2_7: bool
    db_schema_migration_added_by_rf2_7: bool
    visual_qa_runtime_added_by_rf2_7: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_slides_runtime_closure_readiness() -> SlidesRuntimeClosureReadiness:
    """Return the RF2 slides runtime closure/readiness contract.

    RF2.7 is a closure gate. It consolidates RF2.0-RF2.6 readiness and keeps
    Kimi-level product-power work deferred to the later K-phase.
    """

    return SlidesRuntimeClosureReadiness(
        checkpoint="RF2.7",
        closed_checkpoints=RF2_SLIDES_RUNTIME_CHECKPOINTS,
        capabilities=RF2_SLIDES_RUNTIME_CAPABILITIES,
        non_goals_preserved=RF2_SLIDES_RUNTIME_NON_GOALS,
        next_route=RF2_SLIDES_RUNTIME_NEXT_ROUTE,
        approved_plan_runtime_ready=True,
        lifecycle_runtime_ready=True,
        saved_plan_retry_ready=True,
        render_mode_runtime_ready=True,
        provenance_manifest_runtime_ready=True,
        rf2_slides_path_ready_for_closure=True,
        k_phase_ready_to_start=False,
        kimi_grade_supported=False,
        whole_project_kimi_level_supported=False,
        dependency_versions_changed_by_rf2_7=False,
        dockerfiles_changed_by_rf2_7=False,
        api_endpoint_added_by_rf2_7=False,
        db_schema_migration_added_by_rf2_7=False,
        visual_qa_runtime_added_by_rf2_7=False,
    )


def validate_slides_runtime_closure_readiness(
    readiness: SlidesRuntimeClosureReadiness | None = None,
) -> list[str]:
    item = readiness or build_slides_runtime_closure_readiness()
    errors: list[str] = []

    missing_checkpoints = [checkpoint for checkpoint in RF2_SLIDES_RUNTIME_CHECKPOINTS if checkpoint not in item.closed_checkpoints]
    if missing_checkpoints:
        errors.append(f"missing RF2 checkpoint(s): {', '.join(missing_checkpoints)}")

    missing_capabilities = [capability for capability in RF2_SLIDES_RUNTIME_CAPABILITIES if capability not in item.capabilities]
    if missing_capabilities:
        errors.append(f"missing RF2 capability/capabilities: {', '.join(missing_capabilities)}")

    for flag_name in (
        "approved_plan_runtime_ready",
        "lifecycle_runtime_ready",
        "saved_plan_retry_ready",
        "render_mode_runtime_ready",
        "provenance_manifest_runtime_ready",
        "rf2_slides_path_ready_for_closure",
    ):
        if not bool(getattr(item, flag_name)):
            errors.append(f"{flag_name} must be true")

    if item.k_phase_ready_to_start:
        errors.append("RF2.7 must not start K-phase")
    if item.kimi_grade_supported:
        errors.append("RF2.7 must not claim Kimi-grade support")
    if item.whole_project_kimi_level_supported:
        errors.append("RF2.7 must not claim whole-project Kimi-level support")
    if item.dependency_versions_changed_by_rf2_7:
        errors.append("RF2.7 must not change dependency versions")
    if item.dockerfiles_changed_by_rf2_7:
        errors.append("RF2.7 must not change Dockerfiles")
    if item.api_endpoint_added_by_rf2_7:
        errors.append("RF2.7 must not add public API endpoints")
    if item.db_schema_migration_added_by_rf2_7:
        errors.append("RF2.7 must not add DB schema migrations")
    if item.visual_qa_runtime_added_by_rf2_7:
        errors.append("RF2.7 must not add visual QA runtime")

    expected_route = tuple(item.next_route[:5])
    if expected_route != RF2_SLIDES_RUNTIME_NEXT_ROUTE:
        errors.append("RF2.7 next route must remain RF2_closure -> RF3 -> RF4 -> RF_closure -> K0")

    return errors
