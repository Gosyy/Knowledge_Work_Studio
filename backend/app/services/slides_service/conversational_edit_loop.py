from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

S8_WORKFLOW_ID = "slides.conversational_edit_loop"
SUPPORTED_EDIT_INTENTS = (
    "shorten_deck",
    "reframe_for_board",
    "add_risk_slide",
    "replace_table_with_decision_matrix",
    "revise_slide_order",
    "tighten_citations",
    "convert_to_architecture_review",
)
REQUIRED_INPUTS = (
    "saved_plan_snapshot_id",
    "approved_plan_digest",
    "operator_edit_instruction",
    "citation_manifest_id",
)
SAFE_TASK_EVENTS = (
    "slides.conversation.edit.requested",
    "slides.saved_plan_snapshot.loaded",
    "slides.edit.intent.classified",
    "slides.edit.plan_patch.proposed",
    "slides.edit.plan_patch.review_required",
    "slides.edit.plan_patch.approved",
    "slides.citations.revalidation.started",
    "slides.citations.revalidation.completed",
    "slides.generation.from_revised_plan.started",
    "artifact.registered",
    "plan.snapshot.registered",
    "slides.conversation.edit.completed",
)
CITATION_REVALIDATION_REQUIREMENTS = (
    "preserve_existing_valid_citations",
    "invalidate_removed_claim_citations",
    "require_new_citations_for_new_claims",
    "require_native_visual_citation_recheck",
    "require_image_region_citation_recheck",
)
FORBIDDEN_EDIT_SOURCES = (
    "hidden_public_web_lookup",
    "cloud_search_result",
    "cloud_vision_result",
    "unattributed_model_memory",
    "transient_prompt_only_generation",
)


@dataclass(frozen=True)
class ConversationalEditIntentPolicy:
    intent_id: str
    requires_saved_plan: bool = True
    requires_operator_review: bool = True
    citation_revalidation_required: bool = True
    allowed_output_mutations: tuple[str, ...] = ("plan_patch", "citation_revalidation")

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_output_mutations"] = list(self.allowed_output_mutations)
        return payload


@dataclass(frozen=True)
class ConversationalEditLoopContract:
    workflow_id: str
    title: str
    supported_edit_intents: tuple[str, ...]
    required_inputs: tuple[str, ...]
    safe_task_events: tuple[str, ...]
    citation_revalidation_requirements: tuple[str, ...]
    forbidden_edit_sources: tuple[str, ...]
    intent_policies: tuple[ConversationalEditIntentPolicy, ...]
    requires_saved_plan_snapshot: bool
    requires_approved_plan_digest: bool
    requires_explicit_operator_approval: bool
    plan_patch_preview_required: bool
    citation_manifest_required: bool
    citation_revalidation_required: bool
    generation_from_transient_prompt_allowed: bool
    direct_pptx_generation_without_plan_allowed: bool
    undo_or_retry_from_previous_snapshot_required: bool
    offline_ready: bool
    provenance_required: bool
    compatible_with_s2_outline_first: bool
    compatible_with_s7_offline_citations: bool
    hidden_public_internet_allowed: bool
    cloud_research_allowed: bool
    cloud_vision_allowed: bool
    kimi_level_claimed: bool
    server3_local_intranet_verified: bool

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["supported_edit_intents"] = list(self.supported_edit_intents)
        payload["required_inputs"] = list(self.required_inputs)
        payload["safe_task_events"] = list(self.safe_task_events)
        payload["citation_revalidation_requirements"] = list(self.citation_revalidation_requirements)
        payload["forbidden_edit_sources"] = list(self.forbidden_edit_sources)
        payload["intent_policies"] = [p.as_dict() for p in self.intent_policies]
        return payload


INTENT_POLICIES = tuple(ConversationalEditIntentPolicy(intent_id=intent) for intent in SUPPORTED_EDIT_INTENTS)
CONVERSATIONAL_EDIT_LOOP_CONTRACT = ConversationalEditLoopContract(
    workflow_id=S8_WORKFLOW_ID,
    title="Conversational edit loop over saved plan and citation-aware deck revisions",
    supported_edit_intents=SUPPORTED_EDIT_INTENTS,
    required_inputs=REQUIRED_INPUTS,
    safe_task_events=SAFE_TASK_EVENTS,
    citation_revalidation_requirements=CITATION_REVALIDATION_REQUIREMENTS,
    forbidden_edit_sources=FORBIDDEN_EDIT_SOURCES,
    intent_policies=INTENT_POLICIES,
    requires_saved_plan_snapshot=True,
    requires_approved_plan_digest=True,
    requires_explicit_operator_approval=True,
    plan_patch_preview_required=True,
    citation_manifest_required=True,
    citation_revalidation_required=True,
    generation_from_transient_prompt_allowed=False,
    direct_pptx_generation_without_plan_allowed=False,
    undo_or_retry_from_previous_snapshot_required=True,
    offline_ready=True,
    provenance_required=True,
    compatible_with_s2_outline_first=True,
    compatible_with_s7_offline_citations=True,
    hidden_public_internet_allowed=False,
    cloud_research_allowed=False,
    cloud_vision_allowed=False,
    kimi_level_claimed=False,
    server3_local_intranet_verified=False,
)


def validate_conversational_edit_loop_contract(contract: ConversationalEditLoopContract = CONVERSATIONAL_EDIT_LOOP_CONTRACT) -> list[str]:
    errors: list[str] = []
    if contract.workflow_id != S8_WORKFLOW_ID:
        errors.append("workflow_id must be slides.conversational_edit_loop")
    for item in REQUIRED_INPUTS:
        if item not in contract.required_inputs:
            errors.append(f"missing required input: {item}")
    for intent in SUPPORTED_EDIT_INTENTS:
        if intent not in contract.supported_edit_intents:
            errors.append(f"missing supported edit intent: {intent}")
    for event in SAFE_TASK_EVENTS:
        if event not in contract.safe_task_events:
            errors.append(f"missing safe task event: {event}")
    for requirement in CITATION_REVALIDATION_REQUIREMENTS:
        if requirement not in contract.citation_revalidation_requirements:
            errors.append(f"missing citation revalidation requirement: {requirement}")
    for source in FORBIDDEN_EDIT_SOURCES:
        if source not in contract.forbidden_edit_sources:
            errors.append(f"missing forbidden edit source: {source}")
    boolean_requirements = {
        "requires_saved_plan_snapshot": contract.requires_saved_plan_snapshot,
        "requires_approved_plan_digest": contract.requires_approved_plan_digest,
        "requires_explicit_operator_approval": contract.requires_explicit_operator_approval,
        "plan_patch_preview_required": contract.plan_patch_preview_required,
        "citation_manifest_required": contract.citation_manifest_required,
        "citation_revalidation_required": contract.citation_revalidation_required,
        "undo_or_retry_from_previous_snapshot_required": contract.undo_or_retry_from_previous_snapshot_required,
        "offline_ready": contract.offline_ready,
        "provenance_required": contract.provenance_required,
        "compatible_with_s2_outline_first": contract.compatible_with_s2_outline_first,
        "compatible_with_s7_offline_citations": contract.compatible_with_s7_offline_citations,
    }
    for name, value in boolean_requirements.items():
        if value is not True:
            errors.append(f"{name} must be true")
    forbidden_true = {
        "generation_from_transient_prompt_allowed": contract.generation_from_transient_prompt_allowed,
        "direct_pptx_generation_without_plan_allowed": contract.direct_pptx_generation_without_plan_allowed,
        "hidden_public_internet_allowed": contract.hidden_public_internet_allowed,
        "cloud_research_allowed": contract.cloud_research_allowed,
        "cloud_vision_allowed": contract.cloud_vision_allowed,
        "kimi_level_claimed": contract.kimi_level_claimed,
        "server3_local_intranet_verified": contract.server3_local_intranet_verified,
    }
    for name, value in forbidden_true.items():
        if value is not False:
            errors.append(f"{name} must be false")
    for policy in contract.intent_policies:
        if not policy.requires_saved_plan or not policy.requires_operator_review or not policy.citation_revalidation_required:
            errors.append(f"intent policy is unsafe: {policy.intent_id}")
        if not policy.allowed_output_mutations:
            errors.append(f"intent policy lacks mutation allowlist: {policy.intent_id}")
    return errors


def conversational_edit_loop_report() -> dict[str, Any]:
    contract = CONVERSATIONAL_EDIT_LOOP_CONTRACT
    errors = validate_conversational_edit_loop_contract(contract)
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S8_WORKFLOW_ID,
        "s_phase": "S8",
        "conversational_edit_loop_completed_by_s8": not errors,
        "supported_edit_intent_count": len(contract.supported_edit_intents),
        "supported_edit_intents": list(contract.supported_edit_intents),
        "safe_task_event_count": len(contract.safe_task_events),
        "requires_saved_plan_snapshot_by_s8": contract.requires_saved_plan_snapshot,
        "requires_approved_plan_digest_by_s8": contract.requires_approved_plan_digest,
        "requires_explicit_operator_approval_by_s8": contract.requires_explicit_operator_approval,
        "plan_patch_preview_required_by_s8": contract.plan_patch_preview_required,
        "citation_manifest_required_by_s8": contract.citation_manifest_required,
        "citation_revalidation_required_by_s8": contract.citation_revalidation_required,
        "compatible_with_s2_outline_first_by_s8": contract.compatible_with_s2_outline_first,
        "compatible_with_s7_offline_citations_by_s8": contract.compatible_with_s7_offline_citations,
        "generation_from_transient_prompt_allowed_by_s8": contract.generation_from_transient_prompt_allowed,
        "direct_pptx_generation_without_plan_allowed_by_s8": contract.direct_pptx_generation_without_plan_allowed,
        "hidden_public_internet_allowed_by_s8": contract.hidden_public_internet_allowed,
        "cloud_research_allowed_by_s8": contract.cloud_research_allowed,
        "cloud_vision_allowed_by_s8": contract.cloud_vision_allowed,
        "public_internet_required_by_s8": False,
        "offline_ready_by_s8": contract.offline_ready,
        "api_endpoint_added_by_s8": False,
        "db_schema_migration_added_by_s8": False,
        "frontend_runtime_changed_by_s8": False,
        "dependency_versions_changed_by_s8": False,
        "dockerfiles_changed_by_s8": False,
        "kimi_level_claimed_by_s8": contract.kimi_level_claimed,
        "whole_project_kimi_level_supported": False,
        "server3_local_intranet_route_verified_by_s8": contract.server3_local_intranet_verified,
        "next_recommended_step": "S9 - render-based visual QA for actual slide screenshots and layout collision checks.",
        "contract": contract.as_dict(),
        "errors": errors,
    }
