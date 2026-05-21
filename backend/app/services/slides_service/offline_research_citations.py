from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

S7_WORKFLOW_ID = "slides.offline_research_citations"

ALLOWED_SOURCE_TYPES = (
    "uploaded_document",
    "internal_browser_evidence_packet",
    "local_knowledge_base_entry",
    "intranet_document",
    "image_region_evidence",
    "generated_artifact_manifest",
)

FORBIDDEN_SOURCE_TYPES = (
    "hidden_public_web_lookup",
    "cloud_search_result",
    "cloud_vision_result",
    "unattributed_model_memory",
)

REQUIRED_CITATION_FIELDS = (
    "citation_id",
    "source_type",
    "source_id",
    "fragment_id",
    "claim_id",
    "slide_id",
    "evidence_summary",
    "locator",
    "provenance_digest",
)

SUPPORTED_CLAIM_TARGETS = (
    "slide_claim",
    "speaker_note_claim",
    "native_table_cell",
    "native_chart_series",
    "native_diagram_node",
    "image_region_reconstruction",
)

REQUIRED_MANIFEST_SECTIONS = (
    "sources",
    "fragments",
    "slide_claims",
    "citations",
    "coverage_summary",
    "offline_boundary",
)

COVERAGE_THRESHOLDS = {
    "minimum_slide_claim_citation_coverage": 1.0,
    "minimum_native_visual_citation_coverage": 1.0,
    "minimum_image_region_citation_coverage": 1.0,
}


@dataclass(frozen=True)
class OfflineCitationSourcePolicy:
    source_type: str
    allowed: bool
    description: str
    requires_local_locator: bool
    requires_digest: bool
    public_internet_required: bool
    cloud_service_required: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CitationManifestContract:
    workflow_id: str
    title: str
    allowed_source_types: tuple[str, ...]
    forbidden_source_types: tuple[str, ...]
    required_citation_fields: tuple[str, ...]
    supported_claim_targets: tuple[str, ...]
    required_manifest_sections: tuple[str, ...]
    coverage_thresholds: dict[str, float]
    source_policies: tuple[OfflineCitationSourcePolicy, ...]
    slide_level_claims_require_citations: bool
    native_visuals_require_citations: bool
    image_regions_require_citations: bool
    citation_manifest_required: bool
    citation_coverage_report_required: bool
    hidden_public_internet_allowed: bool
    cloud_research_allowed: bool
    cloud_vision_allowed: bool
    offline_ready: bool
    provenance_required: bool
    compatible_with_s4_native_visuals: bool
    compatible_with_s6_image_regions: bool
    kimi_level_claimed: bool
    server3_local_intranet_verified: bool

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_source_types"] = list(self.allowed_source_types)
        payload["forbidden_source_types"] = list(self.forbidden_source_types)
        payload["required_citation_fields"] = list(self.required_citation_fields)
        payload["supported_claim_targets"] = list(self.supported_claim_targets)
        payload["required_manifest_sections"] = list(self.required_manifest_sections)
        payload["source_policies"] = [policy.as_dict() for policy in self.source_policies]
        return payload


SOURCE_POLICIES = (
    OfflineCitationSourcePolicy(
        source_type="uploaded_document",
        allowed=True,
        description="DOCX/PDF/Markdown/text uploaded by the operator and indexed locally.",
        requires_local_locator=True,
        requires_digest=True,
        public_internet_required=False,
        cloud_service_required=False,
    ),
    OfflineCitationSourcePolicy(
        source_type="internal_browser_evidence_packet",
        allowed=True,
        description="Operator-captured internal/intranet browser evidence packet with saved local content.",
        requires_local_locator=True,
        requires_digest=True,
        public_internet_required=False,
        cloud_service_required=False,
    ),
    OfflineCitationSourcePolicy(
        source_type="local_knowledge_base_entry",
        allowed=True,
        description="Local or intranet knowledge base entry already available to the deployment.",
        requires_local_locator=True,
        requires_digest=True,
        public_internet_required=False,
        cloud_service_required=False,
    ),
    OfflineCitationSourcePolicy(
        source_type="intranet_document",
        allowed=True,
        description="Internal document reachable inside the offline/intranet deployment boundary.",
        requires_local_locator=True,
        requires_digest=True,
        public_internet_required=False,
        cloud_service_required=False,
    ),
    OfflineCitationSourcePolicy(
        source_type="image_region_evidence",
        allowed=True,
        description="S6 image/screenshot crop region used as visual evidence for slide reconstruction.",
        requires_local_locator=True,
        requires_digest=True,
        public_internet_required=False,
        cloud_service_required=False,
    ),
    OfflineCitationSourcePolicy(
        source_type="generated_artifact_manifest",
        allowed=True,
        description="Local generated artifact manifest, safe metadata, or provenance report.",
        requires_local_locator=True,
        requires_digest=True,
        public_internet_required=False,
        cloud_service_required=False,
    ),
)

OFFLINE_RESEARCH_CITATION_CONTRACT = CitationManifestContract(
    workflow_id=S7_WORKFLOW_ID,
    title="Offline/intranet research citations for source-grounded slides",
    allowed_source_types=ALLOWED_SOURCE_TYPES,
    forbidden_source_types=FORBIDDEN_SOURCE_TYPES,
    required_citation_fields=REQUIRED_CITATION_FIELDS,
    supported_claim_targets=SUPPORTED_CLAIM_TARGETS,
    required_manifest_sections=REQUIRED_MANIFEST_SECTIONS,
    coverage_thresholds=COVERAGE_THRESHOLDS,
    source_policies=SOURCE_POLICIES,
    slide_level_claims_require_citations=True,
    native_visuals_require_citations=True,
    image_regions_require_citations=True,
    citation_manifest_required=True,
    citation_coverage_report_required=True,
    hidden_public_internet_allowed=False,
    cloud_research_allowed=False,
    cloud_vision_allowed=False,
    offline_ready=True,
    provenance_required=True,
    compatible_with_s4_native_visuals=True,
    compatible_with_s6_image_regions=True,
    kimi_level_claimed=False,
    server3_local_intranet_verified=False,
)


def validate_offline_research_citation_contract(contract: CitationManifestContract = OFFLINE_RESEARCH_CITATION_CONTRACT) -> list[str]:
    errors: list[str] = []
    if contract.workflow_id != S7_WORKFLOW_ID:
        errors.append("workflow_id must be slides.offline_research_citations")
    if not contract.offline_ready:
        errors.append("offline_ready must be true")
    if not contract.provenance_required:
        errors.append("provenance_required must be true")
    if contract.hidden_public_internet_allowed:
        errors.append("hidden public internet must not be allowed")
    if contract.cloud_research_allowed:
        errors.append("cloud research must not be allowed in production default")
    if contract.cloud_vision_allowed:
        errors.append("cloud vision must not be allowed in production default")
    if contract.kimi_level_claimed:
        errors.append("S7 must not claim Kimi-level parity")
    if contract.server3_local_intranet_verified:
        errors.append("S7 must not claim Server 3 local_intranet verification")
    for source_type in ALLOWED_SOURCE_TYPES:
        if source_type not in contract.allowed_source_types:
            errors.append(f"missing allowed source type: {source_type}")
    for source_type in FORBIDDEN_SOURCE_TYPES:
        if source_type not in contract.forbidden_source_types:
            errors.append(f"missing forbidden source type: {source_type}")
        if source_type in contract.allowed_source_types:
            errors.append(f"forbidden source type is also allowed: {source_type}")
    for field in REQUIRED_CITATION_FIELDS:
        if field not in contract.required_citation_fields:
            errors.append(f"missing required citation field: {field}")
    for section in REQUIRED_MANIFEST_SECTIONS:
        if section not in contract.required_manifest_sections:
            errors.append(f"missing required manifest section: {section}")
    for target in SUPPORTED_CLAIM_TARGETS:
        if target not in contract.supported_claim_targets:
            errors.append(f"missing supported claim target: {target}")
    if not contract.slide_level_claims_require_citations:
        errors.append("slide-level claims must require citations")
    if not contract.native_visuals_require_citations:
        errors.append("S4 native visuals must require citations")
    if not contract.image_regions_require_citations:
        errors.append("S6 image regions must require citations")
    if not contract.citation_manifest_required:
        errors.append("citation manifest is required")
    if not contract.citation_coverage_report_required:
        errors.append("citation coverage report is required")
    if not contract.compatible_with_s4_native_visuals:
        errors.append("S7 must be compatible with S4 native visuals")
    if not contract.compatible_with_s6_image_regions:
        errors.append("S7 must be compatible with S6 image regions")
    for key, value in contract.coverage_thresholds.items():
        if float(value) < 1.0:
            errors.append(f"coverage threshold must be complete for {key}")
    policy_by_type = {policy.source_type: policy for policy in contract.source_policies}
    for source_type in ALLOWED_SOURCE_TYPES:
        policy = policy_by_type.get(source_type)
        if policy is None:
            errors.append(f"missing source policy: {source_type}")
            continue
        if not policy.allowed:
            errors.append(f"allowed source policy is disabled: {source_type}")
        if not policy.requires_local_locator:
            errors.append(f"source policy must require local locator: {source_type}")
        if not policy.requires_digest:
            errors.append(f"source policy must require digest: {source_type}")
        if policy.public_internet_required:
            errors.append(f"source policy must not require public internet: {source_type}")
        if policy.cloud_service_required:
            errors.append(f"source policy must not require cloud service: {source_type}")
    return errors


def offline_research_citations_report() -> dict[str, Any]:
    contract = OFFLINE_RESEARCH_CITATION_CONTRACT
    errors = validate_offline_research_citation_contract(contract)
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S7_WORKFLOW_ID,
        "s_phase": "S7",
        "offline_research_citations_completed_by_s7": not errors,
        "citation_manifest_required_by_s7": contract.citation_manifest_required,
        "citation_coverage_report_required_by_s7": contract.citation_coverage_report_required,
        "slide_level_claim_citations_required_by_s7": contract.slide_level_claims_require_citations,
        "native_visual_citations_required_by_s7": contract.native_visuals_require_citations,
        "image_region_citations_required_by_s7": contract.image_regions_require_citations,
        "allowed_source_types": list(contract.allowed_source_types),
        "forbidden_source_types": list(contract.forbidden_source_types),
        "supported_claim_targets": list(contract.supported_claim_targets),
        "required_citation_fields": list(contract.required_citation_fields),
        "required_manifest_sections": list(contract.required_manifest_sections),
        "coverage_thresholds": dict(contract.coverage_thresholds),
        "source_policy_count": len(contract.source_policies),
        "compatible_with_s4_native_visuals_by_s7": contract.compatible_with_s4_native_visuals,
        "compatible_with_s6_image_regions_by_s7": contract.compatible_with_s6_image_regions,
        "hidden_public_internet_allowed_by_s7": contract.hidden_public_internet_allowed,
        "cloud_research_allowed_by_s7": contract.cloud_research_allowed,
        "cloud_vision_allowed_by_s7": contract.cloud_vision_allowed,
        "public_internet_required_by_s7": False,
        "offline_ready_by_s7": contract.offline_ready,
        "api_endpoint_added_by_s7": False,
        "db_schema_migration_added_by_s7": False,
        "frontend_runtime_changed_by_s7": False,
        "dependency_versions_changed_by_s7": False,
        "dockerfiles_changed_by_s7": False,
        "kimi_level_claimed_by_s7": contract.kimi_level_claimed,
        "whole_project_kimi_level_supported": False,
        "server3_local_intranet_route_verified_by_s7": contract.server3_local_intranet_verified,
        "next_recommended_step": "S8 - conversational edit loop over saved plan and citation-aware deck revisions.",
        "contract": contract.as_dict(),
        "errors": errors,
    }
